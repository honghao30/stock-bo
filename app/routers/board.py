"""
게시판 관리 라우터
"""
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import date

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 게시판 설정 데이터 (DB 연결 전)
boards = [
    {
        "id": "B001",
        "name": "자유게시판",
        "type": "korean",
        "auth": "member",
        "created_at": "2024-03-24"
    },
    {
        "id": "B002",
        "name": "문의사항(방명록)",
        "type": "guestbook",
        "auth": "all",
        "created_at": "2024-03-24"
    }
]


@router.get("/admin/board", response_class=HTMLResponse)
async def admin_board_page(request: Request, user=Depends(get_current_user)):
    """게시판 관리 페이지"""
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("board_admin.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "boards": boards,
        "active_page": "board"
    })


@router.post("/admin/board/create")
async def create_board(
    name: str = Form(...),
    type: str = Form(...),
    auth: str = Form(...),
    user=Depends(get_current_user)
):
    """새 게시판 생성"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    new_id = f"B{len(boards) + 1:03d}"
    boards.append({
        "id": new_id,
        "name": name,
        "type": type,
        "auth": auth,
        "created_at": str(date.today())
    })
    return RedirectResponse(url="/admin/board", status_code=303)


@router.post("/admin/board/update")
async def update_board(
    board_id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    auth: str = Form(...),
    user=Depends(get_current_user)
):
    """게시판 설정 수정"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    for b in boards:
        if b['id'] == board_id:
            b['name'] = name
            b['type'] = type
            b['auth'] = auth
            break
    
    return RedirectResponse(url="/admin/board", status_code=303)


@router.get("/admin/board/delete/{board_id}")
async def delete_board(board_id: str, user=Depends(get_current_user)):
    """게시판 삭제"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    global boards
    boards = [b for b in boards if b['id'] != board_id]
    return RedirectResponse(url="/admin/board", status_code=303)

