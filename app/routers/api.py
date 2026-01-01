"""
REST API 라우터 - 프론트엔드용
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app import models
from app.routers.board import parse_attached_files, clean_content
from app.dependencies import get_current_user_from_token

router = APIRouter()


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """datetime을 ISO 형식 문자열로 변환"""
    if dt is None:
        return None
    return dt.isoformat()


def serialize_date(d: Optional[date]) -> Optional[str]:
    """date를 ISO 형식 문자열로 변환"""
    if d is None:
        return None
    return d.isoformat()


# =========================================================
# 게시판 API
# =========================================================

@router.get("/api/boards")
async def get_boards(
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_token)
):
    """
    게시판 목록 조회
    """
    boards = db.query(models.Board).order_by(models.Board.created_at).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": board.id,
                "name": board.name,
                "type": board.type,
                "auth": board.auth,
                "created_at": serialize_datetime(board.created_at),
                "updated_at": serialize_datetime(board.updated_at),
                "post_count": len(board.posts) if board.posts else 0
            }
            for board in boards
        ],
        "count": len(boards)
    }


@router.get("/api/boards/{board_id}")
async def get_board(
    board_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_token)
):
    """
    게시판 상세 조회
    """
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    return {
        "success": True,
        "data": {
            "id": board.id,
            "name": board.name,
            "type": board.type,
            "auth": board.auth,
            "created_at": serialize_datetime(board.created_at),
            "updated_at": serialize_datetime(board.updated_at),
            "post_count": len(board.posts) if board.posts else 0
        }
    }


@router.get("/api/boards/{board_id}/posts")
async def get_board_posts(
    board_id: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_token)
):
    """
    게시판의 게시글 목록 조회 (페이지네이션 지원)
    """
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    # 전체 게시글 수
    total_count = db.query(models.Post).filter(models.Post.board_id == board_id).count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    posts = db.query(models.Post).filter(
        models.Post.board_id == board_id
    ).order_by(models.Post.created_at.desc()).offset(offset).limit(limit).all()
    
    # 게시글 데이터 변환
    posts_data = []
    for post in posts:
        # 첨부파일 정보 파싱
        attachments = parse_attached_files(post.content or "")
        cleaned_content = clean_content(post.content or "")
        
        posts_data.append({
            "id": post.id,
            "board_id": post.board_id,
            "title": post.title,
            "content": cleaned_content,
            "author": post.author,
            "views": post.views or 0,
            "created_at": serialize_datetime(post.created_at),
            "updated_at": serialize_datetime(post.updated_at),
            "attachments": attachments
        })
    
    return {
        "success": True,
        "data": posts_data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 0
        }
    }


@router.get("/api/posts/{post_id}")
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_token)
):
    """
    게시글 상세 조회
    """
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 조회수 증가
    post.views = (post.views or 0) + 1
    db.commit()
    
    # 첨부파일 정보 파싱
    attachments = parse_attached_files(post.content or "")
    cleaned_content = clean_content(post.content or "")
    
    # 게시판 정보도 함께 반환
    board = post.board if post.board else None
    
    return {
        "success": True,
        "data": {
            "id": post.id,
            "board_id": post.board_id,
            "board": {
                "id": board.id,
                "name": board.name,
                "type": board.type
            } if board else None,
            "title": post.title,
            "content": cleaned_content,
            "author": post.author,
            "views": post.views or 0,
            "created_at": serialize_datetime(post.created_at),
            "updated_at": serialize_datetime(post.updated_at),
            "attachments": attachments
        }
    }


# =========================================================
# 일정 관리 API
# =========================================================

@router.get("/api/schedules")
async def get_schedules(
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    type: Optional[str] = Query(None, description="일정 타입 (manual, api)"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_token)
):
    """
    일정 목록 조회 (날짜 범위 및 타입 필터링 지원)
    """
    query = db.query(models.Schedule)
    
    # 날짜 범위 필터링
    if start_date:
        try:
            start = date.fromisoformat(start_date)
            query = query.filter(models.Schedule.date >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 시작 날짜 형식입니다. (YYYY-MM-DD)")
    
    if end_date:
        try:
            end = date.fromisoformat(end_date)
            query = query.filter(models.Schedule.date <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 종료 날짜 형식입니다. (YYYY-MM-DD)")
    
    # 타입 필터링
    if type:
        query = query.filter(models.Schedule.type == type)
    
    schedules = query.order_by(models.Schedule.date).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": schedule.id,
                "date": serialize_date(schedule.date),
                "subject": schedule.subject,
                "content": schedule.content or "",
                "type": schedule.type,
                "created_at": serialize_datetime(schedule.created_at),
                "updated_at": serialize_datetime(schedule.updated_at)
            }
            for schedule in schedules
        ],
        "count": len(schedules)
    }


@router.get("/api/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user_from_token)
):
    """
    일정 상세 조회
    """
    schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    
    return {
        "success": True,
        "data": {
            "id": schedule.id,
            "date": serialize_date(schedule.date),
            "subject": schedule.subject,
            "content": schedule.content or "",
            "type": schedule.type,
            "created_at": serialize_datetime(schedule.created_at),
            "updated_at": serialize_datetime(schedule.updated_at)
        }
    }

