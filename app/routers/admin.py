"""
관리자 관리 라우터
"""
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models, utils
from app.database import get_db
from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """관리자 관리 페이지"""
    if not user:
        return RedirectResponse(url="/")
    
    db_users = db.query(models.AdminUser).all()
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "users": db_users,
        "active_page": "users"
    })


@router.post("/admin/users/add")
async def add_admin(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """관리자 추가"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    if db.query(models.AdminUser).filter(models.AdminUser.email == email).first():
        return HTMLResponse("<script>alert('이미 존재하는 이메일입니다.'); history.back();</script>")
    
    new_admin = models.AdminUser(
        email=email,
        name=name,
        hashed_password=utils.get_password_hash(password)
    )
    db.add(new_admin)
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=303)


@router.get("/admin/users/delete/{email}")
async def delete_admin(
    email: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """관리자 삭제"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if email == ADMIN_EMAIL:
        return HTMLResponse("<script>alert('최고 관리자 계정은 삭제할 수 없습니다.'); location.href='/admin/users';</script>")
    
    target_user = db.query(models.AdminUser).filter(models.AdminUser.email == email).first()
    if target_user:
        db.delete(target_user)
        db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=303)

