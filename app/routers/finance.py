"""
금융위원회 API 라우터
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.services.api_service import finance_api_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/api/fetch-data")
async def fetch_data(user=Depends(get_current_user)):
    """모든 금융위원회 데이터 수집"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    
    try:
        data = await finance_api_service.fetch_all_finance_data()
        return JSONResponse({
            "success": True,
            "message": "데이터 수집이 완료되었습니다.",
            "data": data
        })
    except Exception as e:
        return JSONResponse({"error": f"데이터 수집 중 오류가 발생했습니다: {str(e)}"}, status_code=500)


@router.get("/api/disclosure-info")
async def get_disclosure_info(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    """배당공시정보 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_disclosure_info(page_no, num_of_rows)
    return JSONResponse(data)


@router.get("/api/capital-increase-info")
async def get_capital_increase_info(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    """공모주/유상증자 공시정보 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_capital_increase_info(page_no, num_of_rows)
    return JSONResponse(data)


@router.get("/api/bonus-issuance-info")
async def get_bonus_issuance_info(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    """무상증자 공시정보 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_bonus_issuance_info(page_no, num_of_rows)
    return JSONResponse(data)


@router.get("/api/stock-issuance")
async def get_stock_issuance(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    """주식발행 공시정보 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_stock_issuance_info(page_no, num_of_rows)
    return JSONResponse(data)


@router.get("/api/stock-price")
async def get_stock_price(request: Request, page_no: int = 1, num_of_rows: int = 10, bas_dt: str = None, user=Depends(get_current_user)):
    """주식시세정보 조회"""
    if not user:
        return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_stock_price_info(page_no, num_of_rows, bas_dt)
    return JSONResponse(data)


@router.get("/admin/finance-data", response_class=HTMLResponse)
async def finance_data_page(request: Request, user=Depends(get_current_user)):
    """금융위원회 데이터 확인 페이지"""
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("finance_data.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "active_page": "dashboard"
    })

