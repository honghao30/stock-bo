"""
애플리케이션 설정
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PW = os.environ.get("ADMIN_PW")
AUTH_COOKIE_NAME = os.environ.get("AUTH_COOKIE_NAME", "bo_session_id")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")

# JWT 설정
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_TOKEN or "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_HOURS = 24  # 토큰 만료 시간 (24시간)

