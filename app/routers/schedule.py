"""
일정 관리 라우터
"""
from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date as date_type

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.database import get_db
from app import models
from app.services.schedule_api_service import schedule_api_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/schedule", response_class=HTMLResponse)
async def schedule_page(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """일정 관리 페이지"""
    if not user:
        return RedirectResponse(url="/")
    
    # DB에서 일정 목록 가져오기 (날짜순 정렬)
    schedules = db.query(models.Schedule).order_by(models.Schedule.date).all()
    
    # SQLAlchemy 모델을 딕셔너리로 변환
    schedule_list = [
        {
            "id": s.id,
            "date": s.date.isoformat() if s.date else None,
            "subject": s.subject,
            "content": s.content or "",
            "type": s.type
        }
        for s in schedules
    ]
    
    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "schedules": schedule_list,
        "active_page": "schedule"
    })


@router.post("/admin/schedule/add")
async def add_schedule(
    date: str = Form(...),
    subject: str = Form(...),
    content: str = Form(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """일정 추가"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    try:
        # 날짜 문자열을 date 객체로 변환
        date_obj = date_type.fromisoformat(date)
        
        # 새 일정 생성
        new_schedule = models.Schedule(
            date=date_obj,
            subject=subject,
            content=content or "",
            type="manual"
        )
        
        db.add(new_schedule)
        db.commit()
        db.refresh(new_schedule)
        
        return RedirectResponse(url="/admin/schedule", status_code=303)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"잘못된 날짜 형식: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"일정 추가 실패: {str(e)}")


@router.get("/admin/schedule/delete/{sch_id}")
async def delete_schedule(
    sch_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """일정 삭제"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # 일정 조회
    schedule = db.query(models.Schedule).filter(models.Schedule.id == sch_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    
    try:
        db.delete(schedule)
        db.commit()
        return RedirectResponse(url="/admin/schedule", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"일정 삭제 실패: {str(e)}")


@router.post("/admin/schedule/update")
async def update_schedule(
    sch_id: int = Form(...),
    date: str = Form(...),
    subject: str = Form(...),
    content: str = Form(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """일정 수정"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # 일정 조회
    schedule = db.query(models.Schedule).filter(models.Schedule.id == sch_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
    
    try:
        # 날짜 문자열을 date 객체로 변환
        date_obj = date_type.fromisoformat(date)
        
        # 일정 정보 업데이트
        schedule.date = date_obj
        schedule.subject = subject
        schedule.content = content or ""
        
        db.commit()
        db.refresh(schedule)
        
        return RedirectResponse(url="/admin/schedule", status_code=303)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"잘못된 날짜 형식: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"일정 수정 실패: {str(e)}")


@router.post("/admin/schedule/sync-api")
async def sync_api_schedule(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """API에서 일정 동기화"""
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    try:
        # 외부 API에서 일정 데이터 가져오기
        api_items = await schedule_api_service.fetch_schedules_from_api()
        
        # 가져온 데이터를 DB에 저장
        for item in api_items:
            try:
                # 날짜 문자열을 date 객체로 변환
                date_obj = date_type.fromisoformat(item['date']) if isinstance(item['date'], str) else item['date']
                
                # API 데이터에서 subject와 content 추출 (title이 있으면 subject로 사용)
                subject = item.get('subject') or item.get('title', 'API 일정')
                content = item.get('content', '')
                
                new_schedule = models.Schedule(
                    date=date_obj,
                    subject=subject,
                    content=content,
                    type="api"
                )
                db.add(new_schedule)
            except (ValueError, KeyError) as e:
                print(f"일정 항목 처리 실패: {item}, 오류: {e}")
                continue
        
        db.commit()
        return RedirectResponse(url="/admin/schedule", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"API 동기화 실패: {str(e)}")

