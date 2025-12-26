"""
게시판 관리 라우터
"""
from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.database import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/board", response_class=HTMLResponse)
async def admin_board_page(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """게시판 관리 페이지"""
    if not user:
        return RedirectResponse(url="/")
    
    # DB에서 게시판 목록 가져오기
    boards = db.query(models.Board).order_by(models.Board.created_at).all()
    
    # SQLAlchemy 모델을 딕셔너리로 변환
    board_list = [
        {
            "id": b.id,
            "name": b.name,
            "type": b.type,
            "auth": b.auth,
            "created_at": b.created_at.strftime("%Y-%m-%d") if b.created_at else None
        }
        for b in boards
    ]
    
    return templates.TemplateResponse("board_admin.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "boards": board_list,
        "active_page": "board"
    })


@router.post("/admin/board/create")
async def create_board(
    name: str = Form(...),
    type: str = Form(...),
    auth: str = Form(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 게시판 생성"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    try:
        # 기존 게시판 개수 확인하여 새 ID 생성
        board_count = db.query(models.Board).count()
        new_id = f"B{board_count + 1:03d}"
        
        # ID 중복 확인 (혹시 모를 경우를 대비)
        existing = db.query(models.Board).filter(models.Board.id == new_id).first()
        if existing:
            # 중복이면 다음 번호 시도
            board_count = db.query(models.Board).count()
            new_id = f"B{board_count + 1:03d}"
        
        # 새 게시판 생성
        new_board = models.Board(
            id=new_id,
            name=name,
            type=type,
            auth=auth
        )
        
        db.add(new_board)
        db.commit()
        db.refresh(new_board)
        
        return RedirectResponse(url="/admin/board", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"게시판 생성 실패: {str(e)}")


@router.post("/admin/board/update")
async def update_board(
    board_id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    auth: str = Form(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """게시판 설정 수정"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # 게시판 조회
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    try:
        # 게시판 정보 업데이트
        board.name = name
        board.type = type
        board.auth = auth
        
        db.commit()
        db.refresh(board)
        
        return RedirectResponse(url="/admin/board", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"게시판 수정 실패: {str(e)}")


@router.get("/admin/board/delete/{board_id}")
async def delete_board(
    board_id: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """게시판 삭제"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # 게시판 조회
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    try:
        db.delete(board)
        db.commit()
        return RedirectResponse(url="/admin/board", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"게시판 삭제 실패: {str(e)}")
