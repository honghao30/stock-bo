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

