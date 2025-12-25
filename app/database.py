import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. .env 파일 로드
load_dotenv()

# 2. 환경 변수에서 DB 접속 정보 가져오기
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306") # .env에 53185가 있으면 그걸 씁니다
DB_NAME = os.getenv("DB_NAME", "stock_bo")

# 3. MySQL 연결 URL 생성
# 결과 예시: mysql+pymysql://root:비번@shinkansen.proxy.rlwy.net:53185/railway
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 4. 엔진 생성 (접속 유지 옵션 포함)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()