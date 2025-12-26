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


@router.get("/admin/board/{board_id}/posts", response_class=HTMLResponse)
async def admin_board_posts_page(
    board_id: str,
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """관리자용 게시판 게시글 목록 페이지"""
    if not user:
        return RedirectResponse(url="/")
    
    # 게시판 조회
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    # 게시글 목록 가져오기 (최신순 정렬)
    posts_query = db.query(models.Post).filter(models.Post.board_id == board_id).order_by(models.Post.created_at.desc()).all()
    
    # SQLAlchemy 모델을 딕셔너리로 변환
    posts_list = [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content[:100] + "..." if len(p.content) > 100 else p.content,  # 미리보기
            "author": p.author or "관리자",
            "views": p.views or 0,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else None,
            "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M") if p.updated_at else None
        }
        for p in posts_query
    ]
    
    # 게시판 정보를 딕셔너리로 변환
    board_dict = {
        "id": board.id,
        "name": board.name,
        "type": board.type,
        "auth": board.auth,
        "created_at": board.created_at.strftime("%Y-%m-%d") if board.created_at else None
    }
    
    return templates.TemplateResponse("admin_board_posts.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "board": board_dict,
        "posts": posts_list,
        "active_page": "board"
    })


# --- 일반 사용자용 게시판 페이지 ---

@router.get("/boards", response_class=HTMLResponse)
async def board_list_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """게시판 목록 페이지 (일반 사용자용)"""
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
    
    return templates.TemplateResponse("board_list.html", {
        "request": request,
        "boards": board_list,
        "active_page": None  # 사이드바 비활성화
    })


@router.get("/board/{board_id}", response_class=HTMLResponse)
async def board_detail_page(
    board_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """게시판 상세 페이지 (게시글 목록)"""
    # 게시판 조회
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    # 게시글 목록 가져오기 (최신순 정렬)
    posts_query = db.query(models.Post).filter(models.Post.board_id == board_id).order_by(models.Post.created_at.desc()).all()
    
    # SQLAlchemy 모델을 딕셔너리로 변환
    posts_list = [
        {
            "id": p.id,
            "title": p.title,
            "author": p.author or "관리자",
            "views": p.views or 0,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else None
        }
        for p in posts_query
    ]
    
    # 게시판 정보를 딕셔너리로 변환
    board_dict = {
        "id": board.id,
        "name": board.name,
        "type": board.type,
        "auth": board.auth,
        "created_at": board.created_at.strftime("%Y-%m-%d") if board.created_at else None
    }
    
    return templates.TemplateResponse("board_detail.html", {
        "request": request,
        "board": board_dict,
        "posts": posts_list,
        "active_page": None  # 사이드바 비활성화
    })


@router.get("/board/{board_id}/write", response_class=HTMLResponse)
async def public_write_post_redirect(
    board_id: str,
    request: Request,
    user=Depends(get_current_user)
):
    """일반 사용자용 글쓰기 페이지 접근 시 관리자 인증 확인 후 리다이렉트"""
    # 관리자가 로그인되어 있으면 관리자용 글쓰기 페이지로 리다이렉트
    if user:
        return RedirectResponse(url=f"/admin/board/{board_id}/write", status_code=303)
    
    # 관리자가 아니면 게시판 목록으로 리다이렉트
    return RedirectResponse(url=f"/board/{board_id}", status_code=303)
