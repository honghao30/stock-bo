"""
회원 관리 라우터
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 가상 회원 데이터 (구글 로그인 회원 가정)
members = [
    {"id": 1, "name": "김철수", "email": "chulsoo@gmail.com", "join_date": "2024-03-20", "status": "active", "posts": 5, "comments": 12},
    {"id": 2, "name": "이영희", "email": "younghee@gmail.com", "join_date": "2024-03-22", "status": "active", "posts": 2, "comments": 45}
]


@router.get("/admin/members", response_class=HTMLResponse)
async def admin_members_page(request: Request, user=Depends(get_current_user)):
    """회원 관리 페이지"""
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("members.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "members": members,
        "active_page": "members"
    })


@router.get("/admin/members/status/{member_id}")
async def toggle_member_status(member_id: int, user=Depends(get_current_user)):
    """회원 상태 토글 (정지/활성화)"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    for m in members:
        if m['id'] == member_id:
            m['status'] = "blocked" if m['status'] == "active" else "active"
            break
    return RedirectResponse(url="/admin/members", status_code=303)

