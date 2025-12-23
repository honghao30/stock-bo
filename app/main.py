from fastapi import FastAPI
# 아래처럼 점(.)이나 app. 없이 임포트하려면 실행 시 경로 설정이 중요합니다.
from app.database import engine, Base
from app import models

app = FastAPI()

# DB 연결 확인용 로직
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)