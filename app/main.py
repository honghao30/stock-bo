"""
FastAPI 애플리케이션 메인 파일
"""
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from app import models
from app.database import engine, get_db
from app import utils
from app.config import ADMIN_EMAIL, ADMIN_PW

# 라우터 import
from app.routers import auth, dashboard, admin, members, board, schedule, finance

# FastAPI 앱 생성
app = FastAPI()

# DB 초기화: 서버 시작 시 테이블 생성
models.Base.metadata.create_all(bind=engine)


def init_admin_user():
    """초기 관리자 계정 자동 생성 함수 (DB가 비어있을 때 실행)"""
    db = next(get_db())
    try:
        if ADMIN_EMAIL and ADMIN_PW:
            existing_user = db.query(models.AdminUser).filter(models.AdminUser.email == ADMIN_EMAIL).first()
            if not existing_user:
                print(f"⚠️ 초기 관리자 계정 생성 중: {ADMIN_EMAIL}")
                hashed_pw = utils.get_password_hash(ADMIN_PW)
                new_admin = models.AdminUser(email=ADMIN_EMAIL, name="최고관리자", hashed_password=hashed_pw)
                db.add(new_admin)
                db.commit()
                print("✅ 초기 관리자 생성 완료")
    except Exception as e:
        print(f"❌ 초기 관리자 생성 실패: {e}")
    finally:
        db.close()


# 서버 실행 시 관리자 체크 실행
init_admin_user()

# 라우터 등록
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(members.router)
app.include_router(board.router)
app.include_router(schedule.router)
app.include_router(finance.router)
