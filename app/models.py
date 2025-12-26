from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.sql import func
from app.database import Base

# Base를 export하여 main.py에서 사용할 수 있도록 함
__all__ = ["Base", "CollectedData", "AdminUser", "Schedule", "Board"]

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

# [신규] 일정 모델
class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)  # 일정 날짜
    subject = Column(String(255), nullable=False)  # 일정 제목
    content = Column(String(500))  # 일정 내용 (선택적)
    type = Column(String(20), default="manual")  # 'manual' 또는 'api'
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 생성일시
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # 수정일시

# [신규] 게시판 모델
class Board(Base):
    __tablename__ = "boards"
    
    id = Column(String(20), primary_key=True, index=True)  # B001, B002 형식
    name = Column(String(100), nullable=False)  # 게시판 이름
    type = Column(String(20), nullable=False)  # 'korean' 또는 'guestbook'
    auth = Column(String(20), nullable=False, default="all")  # 'all', 'member', 'admin'
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 생성일시
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # 수정일시