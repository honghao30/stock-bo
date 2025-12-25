from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

# (기존) 수집 데이터 모델
class CollectedData(Base):
    __tablename__ = "collected_data"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50))
    status = Column(String(20))
    message = Column(String(255)) # Text 대신 String 사용 권장 (MySQL 호환성)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# [신규] 관리자 사용자 모델
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True) # 이메일 중복 방지
    name = Column(String(50))
    hashed_password = Column(String(255)) # 암호화된 비밀번호 저장
    created_at = Column(DateTime(timezone=True), server_default=func.now())