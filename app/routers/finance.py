"""
한국거래소(KRX) API 라우터
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.services.api_service import krx_api_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/api/krx-kospi")
async def get_krx_kospi(request: Request, bas_dd: str = None, user=Depends(get_current_user)):
    """한국거래소 코스피 지수 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await krx_api_service.fetch_kospi_index(bas_dd)
    return JSONResponse(data)


@router.get("/api/krx-kosdaq")
async def get_krx_kosdaq(request: Request, bas_dd: str = None, user=Depends(get_current_user)):
    """한국거래소 코스닥 지수 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await krx_api_service.fetch_kosdaq_index(bas_dd)
    return JSONResponse(data)


@router.get("/api/krx-market")
async def get_krx_market(request: Request, bas_dd: str = None, user=Depends(get_current_user)):
    """한국거래소 전체 시장 지수 조회 (코스피 + 코스닥)"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    
    # 코스피와 코스닥 데이터를 모두 가져옴
    kospi_data = await krx_api_service.fetch_kospi_index(bas_dd)
    kosdaq_data = await krx_api_service.fetch_kosdaq_index(bas_dd)
    
    return JSONResponse({
        "kospi": kospi_data,
        "kosdaq": kosdaq_data
    })


@router.get("/admin/finance-data", response_class=HTMLResponse)
async def finance_data_page(request: Request, user=Depends(get_current_user)):
    """금융위원회 데이터 확인 페이지"""
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("finance_data.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "active_page": "finance-data"
    })

