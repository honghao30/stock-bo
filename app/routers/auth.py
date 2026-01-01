"""
인증 관련 라우터
"""
from fastapi import APIRouter, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta

from app import models, utils
from app.database import get_db
from app.dependencies import get_current_user, AUTH_COOKIE_NAME, SECRET_TOKEN
from app.config import ADMIN_EMAIL

router = APIRouter()


# API 토큰 발급용 요청 모델
class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.get("/", response_class=HTMLResponse)
async def read_root(user=Depends(get_current_user)):
    """초기 접속 화면 - 로그인 시 대시보드로 리다이렉트"""
    if user:
        return RedirectResponse(url="/admin/dashboard")
    # 로그인되지 않은 경우 로그인 페이지로 리다이렉트
    return RedirectResponse(url="/login")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """로그인 화면"""
    if request.cookies.get(AUTH_COOKIE_NAME) == SECRET_TOKEN:
        return RedirectResponse(url="/admin/dashboard")
    return """
    <div style="width: 350px; margin: 100px auto; padding: 30px; border: 1px solid #ddd; border-radius: 12px; font-family: sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; color: #333;">관리자 로그인 (BO)</h2>
        <form action="/login" method="post" style="display: flex; flex-direction: column; gap: 15px;">
            <input type="email" name="username" placeholder="이메일" required style="padding: 12px; border: 1px solid #ccc; border-radius: 6px;">
            <input type="password" name="password" placeholder="비밀번호" required style="padding: 12px; border: 1px solid #ccc; border-radius: 6px;">
            <button type="submit" style="padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer;">로그인</button>
        </form>
    </div>
    """


@router.post("/login")
async def do_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """로그인 처리"""
    user = db.query(models.AdminUser).filter(models.AdminUser.email == username).first()
    
    if not user or not utils.verify_password(password, user.hashed_password):
        return HTMLResponse("<script>alert('아이디 또는 비밀번호가 잘못되었습니다.'); window.location.href='/login';</script>")
    
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key=AUTH_COOKIE_NAME, value=SECRET_TOKEN, httponly=True)
    return response


@router.get("/logout")
async def logout():
    """로그아웃"""
    response = RedirectResponse(url="/")
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response


# =========================================================
# REST API용 토큰 발급 엔드포인트
# =========================================================

@router.post("/api/auth/login", response_model=TokenResponse)
async def api_login(
    token_request: TokenRequest,
    db: Session = Depends(get_db)
):
    """
    API용 로그인 엔드포인트 (JWT 토큰 발급)
    
    사용 예시:
    ```json
    POST /api/auth/login
    {
        "username": "admin@example.com",
        "password": "password123"
    }
    ```
    
    응답:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 86400
    }
    ```
    """
    user = db.query(models.AdminUser).filter(models.AdminUser.email == token_request.username).first()
    
    if not user or not utils.verify_password(token_request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT 토큰 생성
    access_token_expires = timedelta(hours=24)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }

