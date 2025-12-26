"""
게시판 관리 라우터
"""
from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime  # [수정] date 대신 datetime 사용

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.database import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# =========================================================
# [관리자용] 게시판 관리 (기존 유지)
# =========================================================

@router.get("/admin/board", response_class=HTMLResponse)
async def admin_board_page(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    boards = db.query(models.Board).order_by(models.Board.created_at).all()
    return templates.TemplateResponse("board_admin.html", {
        "request": request, "admin_email": ADMIN_EMAIL, "boards": boards, "active_page": "board"
    })

@router.post("/admin/board/create")
async def create_board(name: str = Form(...), type: str = Form(...), auth: str = Form(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    try:
        cnt = db.query(models.Board).count()
        new_id = f"B{cnt + 1:03d}"
        while db.query(models.Board).filter(models.Board.id == new_id).first():
            cnt += 1
            new_id = f"B{cnt + 1:03d}"
        
        db.add(models.Board(id=new_id, name=name, type=type, auth=auth))
        db.commit()
        return RedirectResponse(url="/admin/board", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/board/update")
async def update_board(board_id: str = Form(...), name: str = Form(...), type: str = Form(...), auth: str = Form(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board:
        board.name = name
        board.type = type
        board.auth = auth
        db.commit()
    return RedirectResponse(url="/admin/board", status_code=303)

@router.get("/admin/board/delete/{board_id}")
async def delete_board(board_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board:
        db.delete(board)
        db.commit()
    return RedirectResponse(url="/admin/board", status_code=303)

@router.get("/admin/board/{board_id}/posts", response_class=HTMLResponse)
async def admin_board_posts_page(board_id: str, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board: raise HTTPException(status_code=404)
    posts = db.query(models.Post).filter(models.Post.board_id == board_id).order_by(models.Post.created_at.desc()).all()
    return templates.TemplateResponse("admin_board_posts.html", {
        "request": request, "admin_email": ADMIN_EMAIL, "board": board, "posts": posts, "active_page": "board"
    })

# --- 관리자 게시글 CRUD (생략 가능하나, 관리자 기능 유지를 위해 포함) ---
@router.get("/admin/board/{board_id}/write", response_class=HTMLResponse)
async def admin_write_post_page(board_id: str, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    return templates.TemplateResponse("admin_post_write.html", {"request": request, "board": board})

@router.post("/admin/board/{board_id}/write")
async def admin_create_post(board_id: str, title: str = Form(...), content: str = Form(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    db.add(models.Post(board_id=board_id, title=title, content=content, author=ADMIN_EMAIL, created_at=datetime.now()))
    db.commit()
    return RedirectResponse(url=f"/admin/board/{board_id}/posts", status_code=303)


# =========================================================
# [사용자용] 게시판 & 방명록 (핵심 로직)
# =========================================================

@router.get("/boards", response_class=HTMLResponse)
async def board_list_page(request: Request, db: Session = Depends(get_db)):
    """게시판 목록 (메인)"""
    boards = db.query(models.Board).order_by(models.Board.created_at).all()
    return templates.TemplateResponse("board_list.html", {"request": request, "boards": boards})


@router.get("/board/{board_id}", response_class=HTMLResponse)
async def board_detail_page(
    board_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    게시판 상세 화면
    - 방명록형: [입력폼] -> [최신글 목록]
    - 일반형: [글쓰기 버튼] -> [제목 목록]
    """
    # 1. 게시판 정보 조회
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    # 2. 게시글 목록 조회 (최신순 정렬: created_at desc)
    posts = db.query(models.Post).filter(
        models.Post.board_id == board_id
    ).order_by(models.Post.created_at.desc()).all()
    
    return templates.TemplateResponse("board_detail.html", {
        "request": request,
        "board": board,
        "posts": posts,
    })


@router.post("/board/write")
async def public_create_post(
    board_id: str = Form(...),
    writer: str = Form(...),          # 작성자 이름
    content: str = Form(...),         # 내용
    password: str = Form(None),       # 비밀번호 (선택)
    title: str = Form(None),          # 제목 (방명록은 없을 수 있음)
    db: Session = Depends(get_db)
):
    """
    사용자 글쓰기 처리 (일반글 & 방명록 공통)
    """
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    # 제목 처리: 방명록은 제목이 없으므로 자동 생성
    final_title = title
    if not final_title:
        if board.type == "guestbook":
            # 내용의 앞 20자를 제목으로 사용
            final_title = content[:20] + "..." if len(content) > 20 else content
        else:
            final_title = "무제"

    # DB 저장
    new_post = models.Post(
        board_id=board_id,
        title=final_title,
        content=content,
        author=writer,
        created_at=datetime.now() # 현재 시간 저장
    )
    
    db.add(new_post)
    db.commit()
    
    # 작성 후 다시 해당 게시판 페이지로 이동 (새로고침 효과)
    return RedirectResponse(url=f"/board/{board_id}", status_code=303)


# 일반형 게시판: 글쓰기 페이지 (방명록 아닐 때만 사용)
@router.get("/board/{board_id}/write", response_class=HTMLResponse)
async def public_write_page_view(board_id: str, request: Request, db: Session = Depends(get_db)):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    return templates.TemplateResponse("post_write_public.html", {"request": request, "board": board})

# 일반형 게시판: 상세 보기 페이지
@router.get("/board/{board_id}/post/{post_id}", response_class=HTMLResponse)
async def public_post_view_page(board_id: str, post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post: raise HTTPException(status_code=404)
    
    # 조회수 증가
    post.views = (post.views or 0) + 1
    db.commit()
    
    return templates.TemplateResponse("post_view.html", {"request": request, "board": {"id": board_id}, "post": post})