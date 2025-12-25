"""
인증 관련 라우터
"""
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app import models, utils
from app.database import get_db
from app.dependencies import get_current_user, AUTH_COOKIE_NAME, SECRET_TOKEN
from app.config import ADMIN_EMAIL

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_root(user=Depends(get_current_user)):
    """초기 접속 화면"""
    if user:
        return RedirectResponse(url="/admin/dashboard")
    return """
    <div style="text-align:center; padding:100px; font-family:sans-serif;">
        <h1 style="color:#e74c3c;">🛑 관리자 인증 필요</h1>
        <p style="font-size:18px; color:#555;">허가되지 않은 접근입니다. 로그인 후 이용해주세요.</p>
        <br>
        <a href="/login" style="padding:15px 30px; background:#3498db; color:white; text-decoration:none; border-radius:8px; font-weight:bold;">로그인 페이지로 이동</a>
    </div>
    """


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

