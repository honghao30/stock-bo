"""
대시보드 라우터
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user=Depends(get_current_user)):
    """관리자 대시보드"""
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "active_page": "dashboard"
    })

