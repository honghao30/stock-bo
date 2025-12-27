"""
공통 의존성 함수들
"""
import os
import json
from fastapi import Request, Depends
from dotenv import load_dotenv

load_dotenv()

AUTH_COOKIE_NAME = os.environ.get("AUTH_COOKIE_NAME", "bo_session_id")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")
MEMBER_COOKIE_NAME = "member_session"


async def get_current_user(request: Request):
    """인증 확인 함수"""
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

