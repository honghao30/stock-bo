"""
공통 의존성 함수들
"""
import os
import json
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.utils import verify_token

load_dotenv()

AUTH_COOKIE_NAME = os.environ.get("AUTH_COOKIE_NAME", "bo_session_id")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")
MEMBER_COOKIE_NAME = "member_session"

# Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(request: Request):
    """인증 확인 함수 (Cookie 기반 - 웹용)"""
    session_id = request.cookies.get(AUTH_COOKIE_NAME)
    if not session_id or session_id != SECRET_TOKEN:
        return None
    return session_id


async def get_current_member(request: Request):
    """회원 세션 확인 함수"""
    member_cookie = request.cookies.get(MEMBER_COOKIE_NAME)
    if not member_cookie:
        return None
    try:
        member_data = json.loads(member_cookie)
        return member_data
    except:
        return None


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    JWT 토큰에서 사용자 정보를 가져오는 함수 (API용)
    Authorization: Bearer <token> 형식으로 요청해야 함
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 정보가 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # DB에서 사용자 확인
    user = db.query(models.AdminUser).filter(models.AdminUser.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

