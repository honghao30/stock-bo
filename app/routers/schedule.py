"""
일정 관리 라우터
"""
from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.services.schedule_api_service import schedule_api_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 일정 데이터 샘플 (아직 DB 연결 안 함, 추후 변경 가능)
schedules = [
    {"id": 1, "date": "2024-03-25", "title": "시스템 정기 점검", "type": "manual"},
    {"id": 2, "date": "2024-03-26", "title": "API 데이터 자동 수집", "type": "api"}
]


@router.get("/admin/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, user=Depends(get_current_user)):
    """일정 관리 페이지"""
    if not user:
        return RedirectResponse(url="/")
    sorted_schedules = sorted(schedules, key=lambda x: x['date'])
    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "schedules": sorted_schedules,
        "active_page": "schedule"
    })


@router.post("/admin/schedule/add")
async def add_schedule(date: str = Form(...), title: str = Form(...), user=Depends(get_current_user)):
    """일정 추가"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    new_id = max([s['id'] for s in schedules], default=0) + 1
    schedules.append({"id": new_id, "date": date, "title": title, "type": "manual"})
    return RedirectResponse(url="/admin/schedule", status_code=303)


@router.get("/admin/schedule/delete/{sch_id}")
async def delete_schedule(sch_id: int, user=Depends(get_current_user)):
    """일정 삭제"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    global schedules
    schedules = [s for s in schedules if s['id'] != sch_id]
    return RedirectResponse(url="/admin/schedule", status_code=303)


@router.post("/admin/schedule/update")
async def update_schedule(
    sch_id: int = Form(...),
    date: str = Form(...),
    title: str = Form(...),
    user=Depends(get_current_user)
):
    """일정 수정"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    global schedules
    for s in schedules:
        if s['id'] == sch_id:
            s['date'] = date
            s['title'] = title
            break
    
    return RedirectResponse(url="/admin/schedule", status_code=303)


@router.post("/admin/schedule/sync-api")
async def sync_api_schedule(user=Depends(get_current_user)):
    """API에서 일정 동기화"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    api_items = await schedule_api_service.fetch_schedules_from_api()
    for item in api_items:
        new_id = max([s['id'] for s in schedules], default=0) + 1
        schedules.append({"id": new_id, "date": item['date'], "title": item['title'], "type": "api"})
    return RedirectResponse(url="/admin/schedule", status_code=303)

