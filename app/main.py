import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session  # [추가] DB 세션 관리

# [추가] utils(암호화), models(테이블), database(연결) 모듈 import
from app import models, utils
from app.database import engine, get_db

# 서비스 모듈 import
from app.services.api_service import finance_api_service
from app.services.schedule_api_service import schedule_api_service

# .env 파일 로드
load_dotenv()

app = FastAPI()

# --- [DB 초기화] 서버 시작 시 테이블 생성 및 초기 관리자 등록 ---
models.Base.metadata.create_all(bind=engine)

# 환경 변수 로드
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PW = os.environ.get("ADMIN_PW")
AUTH_COOKIE_NAME = os.environ.get("AUTH_COOKIE_NAME", "bo_session_id")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")

# 초기 관리자 계정 자동 생성 함수 (DB가 비어있을 때 실행)
def init_admin_user():
    # DB 세션을 수동으로 생성하여 처리
    db = next(get_db())
    try:
        if ADMIN_EMAIL and ADMIN_PW:
            existing_user = db.query(models.AdminUser).filter(models.AdminUser.email == ADMIN_EMAIL).first()
            if not existing_user:
                print(f"⚠️ 초기 관리자 계정 생성 중: {ADMIN_EMAIL}")
                hashed_pw = utils.get_password_hash(ADMIN_PW)
                new_admin = models.AdminUser(email=ADMIN_EMAIL, name="최고관리자", hashed_password=hashed_pw)
                db.add(new_admin)
                db.commit()
                print("✅ 초기 관리자 생성 완료")
    except Exception as e:
        print(f"❌ 초기 관리자 생성 실패: {e}")
    finally:
        db.close()

# 서버 실행 시 관리자 체크 실행
init_admin_user()

# templates 폴더 위치 확인
templates = Jinja2Templates(directory="templates")

# 일정 데이터 샘플 (아직 DB 연결 안 함, 추후 변경 가능)
schedules = [
    {"id": 1, "date": "2024-03-25", "title": "시스템 정기 점검", "type": "manual"},
    {"id": 2, "date": "2024-03-26", "title": "API 데이터 자동 수집", "type": "api"}
]

# 2. 인증 확인 함수
async def get_current_user(request: Request):
    session_id = request.cookies.get(AUTH_COOKIE_NAME)
    if not session_id or session_id != SECRET_TOKEN:
        return None
    return session_id

# 3. [GET] / : 초기 접속 화면
@app.get("/", response_class=HTMLResponse)
async def read_root(user=Depends(get_current_user)):
    if user: return RedirectResponse(url="/admin/dashboard")
    return """
    <div style="text-align:center; padding:100px; font-family:sans-serif;">
        <h1 style="color:#e74c3c;">🛑 관리자 인증 필요</h1>
        <p style="font-size:18px; color:#555;">허가되지 않은 접근입니다. 로그인 후 이용해주세요.</p>
        <br>
        <a href="/login" style="padding:15px 30px; background:#3498db; color:white; text-decoration:none; border-radius:8px; font-weight:bold;">로그인 페이지로 이동</a>
    </div>
    """

# 4. [GET] /login : 로그인 화면
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.cookies.get(AUTH_COOKIE_NAME) == SECRET_TOKEN:
        return RedirectResponse(url="/admin/dashboard")
    return """
    <div style="width: 350px; margin: 100px auto; padding: 30px; border: 1px solid #ddd; border-radius: 12px; font-family: sans-serif; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; color: #333;">관리자 로그인 (BO)</h2>
        <form action="/login" method="post" style="display: flex; flex-direction: column; gap: 15px;">
            <input type="email" name="username" placeholder="이메일" required style="padding: 12px; border: 1px solid #ccc; border-radius: 6px;">
            <input type="password" name="password" placeholder="비밀번호" required style="padding: 12px; border: 1px solid #ccc; border-radius: 6px;">
            <button type="submit" style="padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer;">로그인</button>
        </form>
    </div>
    """

# 5. [POST] /login : 로그인 처리 (DB 연동 적용됨)
@app.post("/login")
async def do_login(
    username: str = Form(...), 
    password: str = Form(...),
    db: Session = Depends(get_db) # DB 주입
):
    # 1. DB에서 사용자 조회
    user = db.query(models.AdminUser).filter(models.AdminUser.email == username).first()
    
    # 2. 사용자 검증 (존재 여부 및 비밀번호 일치 여부)
    if not user or not utils.verify_password(password, user.hashed_password):
        return HTMLResponse("<script>alert('아이디 또는 비밀번호가 잘못되었습니다.'); window.location.href='/login';</script>")
    
    # 3. 로그인 성공 처리
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key=AUTH_COOKIE_NAME, value=SECRET_TOKEN, httponly=True)
    return response

# 6. [GET] /admin/dashboard : 관리자 대시보드
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/")
    return templates.TemplateResponse("dashboard.html", {"request": request, "admin_email": ADMIN_EMAIL, "active_page": "dashboard"})

# --- 관리자 관리 로직 (DB 연동 적용됨) ---

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request, 
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user: return RedirectResponse(url="/")
    
    # DB에서 모든 관리자 조회
    db_users = db.query(models.AdminUser).all()
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request, 
        "admin_email": ADMIN_EMAIL, 
        "users": db_users, 
        "active_page": "users"
    })

@app.post("/admin/users/add")
async def add_admin(
    name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    # 중복 이메일 체크
    if db.query(models.AdminUser).filter(models.AdminUser.email == email).first():
        return HTMLResponse("<script>alert('이미 존재하는 이메일입니다.'); history.back();</script>")
    
    # DB 저장 (비밀번호 암호화)
    new_admin = models.AdminUser(
        email=email, 
        name=name, 
        hashed_password=utils.get_password_hash(password)
    )
    db.add(new_admin)
    db.commit()
    
    return RedirectResponse(url="/admin/users", status_code=303)

@app.get("/admin/users/delete/{email}")
async def delete_admin(
    email: str, 
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user: return RedirectResponse(url="/", status_code=303)
    if email == ADMIN_EMAIL: # 환경변수에 지정된 최고관리자는 삭제 불가 (선택사항)
        return HTMLResponse("<script>alert('최고 관리자 계정은 삭제할 수 없습니다.'); location.href='/admin/users';</script>")
    
    # DB에서 사용자 찾아 삭제
    target_user = db.query(models.AdminUser).filter(models.AdminUser.email == email).first()
    if target_user:
        db.delete(target_user)
        db.commit()
        
    return RedirectResponse(url="/admin/users", status_code=303)

# --- 📅 일정 관리 로직 (기존 유지) ---

@app.get("/admin/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/")
    sorted_schedules = sorted(schedules, key=lambda x: x['date'])
    return templates.TemplateResponse("schedule.html", {
        "request": request, 
        "admin_email": ADMIN_EMAIL, 
        "schedules": sorted_schedules,
        "active_page": "schedule"
    })

@app.post("/admin/schedule/add")
async def add_schedule(date: str = Form(...), title: str = Form(...), user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/", status_code=303)
    new_id = max([s['id'] for s in schedules], default=0) + 1
    schedules.append({"id": new_id, "date": date, "title": title, "type": "manual"})
    return RedirectResponse(url="/admin/schedule", status_code=303)

@app.get("/admin/schedule/delete/{sch_id}")
async def delete_schedule(sch_id: int, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/", status_code=303)
    global schedules
    schedules = [s for s in schedules if s['id'] != sch_id]
    return RedirectResponse(url="/admin/schedule", status_code=303)

@app.post("/admin/schedule/update")
async def update_schedule(
    sch_id: int = Form(...),
    date: str = Form(...),
    title: str = Form(...),
    user=Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    global schedules
    for s in schedules:
        if s['id'] == sch_id:
            s['date'] = date
            s['title'] = title
            break
            
    return RedirectResponse(url="/admin/schedule", status_code=303)

@app.post("/admin/schedule/sync-api")
async def sync_api_schedule(user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/", status_code=303)
    api_items = await schedule_api_service.fetch_schedules_from_api()
    for item in api_items:
        new_id = max([s['id'] for s in schedules], default=0) + 1
        schedules.append({"id": new_id, "date": item['date'], "title": item['title'], "type": "api"})
    return RedirectResponse(url="/admin/schedule", status_code=303)

# --- 금융위원회 API 데이터 수집 엔드포인트 ---
@app.get("/api/fetch-data")
async def fetch_data(user=Depends(get_current_user)):
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

@app.get("/api/disclosure-info")
async def get_disclosure_info(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    if not user: return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_disclosure_info(page_no, num_of_rows)
    return JSONResponse(data)

@app.get("/api/capital-increase-info")
async def get_capital_increase_info(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    if not user: return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_capital_increase_info(page_no, num_of_rows)
    return JSONResponse(data)

@app.get("/api/bonus-issuance-info")
async def get_bonus_issuance_info(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    if not user: return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_bonus_issuance_info(page_no, num_of_rows)
    return JSONResponse(data)

@app.get("/api/stock-issuance")
async def get_stock_issuance(request: Request, page_no: int = 1, num_of_rows: int = 10, user=Depends(get_current_user)):
    if not user: return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_stock_issuance_info(page_no, num_of_rows)
    return JSONResponse(data)

@app.get("/api/stock-price")
async def get_stock_price(request: Request, page_no: int = 1, num_of_rows: int = 10, bas_dt: str = None, user=Depends(get_current_user)):
    if not user: return JSONResponse({"error": "인증이 필요합니다."}, status_code=401)
    data = await finance_api_service.fetch_stock_price_info(page_no, num_of_rows, bas_dt)
    return JSONResponse(data)

# --- 금융위원회 데이터 확인 페이지 ---
@app.get("/admin/finance-data", response_class=HTMLResponse)
async def finance_data_page(request: Request, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/")
    return templates.TemplateResponse("finance_data.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "active_page": "dashboard"
    })

# 7. [GET] /logout : 로그아웃
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response

# --- 가상 회원 데이터 (구글 로그인 회원 가정) ---
members = [
    {"id": 1, "name": "김철수", "email": "chulsoo@gmail.com", "join_date": "2024-03-20", "status": "active", "posts": 5, "comments": 12},
    {"id": 2, "name": "이영희", "email": "younghee@gmail.com", "join_date": "2024-03-22", "status": "active", "posts": 2, "comments": 45}
]

# [GET] 회원 관리 페이지
@app.get("/admin/members", response_class=HTMLResponse)
async def admin_members_page(request: Request, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/")
    return templates.TemplateResponse("members.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "members": members,
        "active_page": "members"
    })

# [GET] 회원 상태 토글 (정지/활성화)
@app.get("/admin/members/status/{member_id}")
async def toggle_member_status(member_id: int, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/", status_code=303)
    for m in members:
        if m['id'] == member_id:
            m['status'] = "blocked" if m['status'] == "active" else "active"
            break
    return RedirectResponse(url="/admin/members", status_code=303)    


# --- 게시판 설정 데이터 (DB 연결 전) ---
boards = [
    {
        "id": "B001", 
        "name": "자유게시판", 
        "type": "korean",  # 일반 한국형
        "auth": "member",  # 회원 전용
        "created_at": "2024-03-24"
    },
    {
        "id": "B002", 
        "name": "문의사항(방명록)", 
        "type": "guestbook", # 방명록(댓글/대댓글 최적화)
        "auth": "all",      # 비회원 가능
        "created_at": "2024-03-24"
    }
]

# [GET] 게시판 관리 메인 (목록 및 생성 폼)
@app.get("/admin/board", response_class=HTMLResponse)
async def admin_board_page(request: Request, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/")
    return templates.TemplateResponse("board_admin.html", {
        "request": request,
        "admin_email": ADMIN_EMAIL,
        "boards": boards,
        "active_page": "board"
    })

# [POST] 새 게시판 생성
@app.post("/admin/board/create")
async def create_board(
    name: str = Form(...),
    type: str = Form(...),
    auth: str = Form(...),
    user=Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    new_id = f"B{len(boards) + 1:03d}"
    from datetime import date
    
    boards.append({
        "id": new_id,
        "name": name,
        "type": type,
        "auth": auth,
        "created_at": str(date.today())
    })
    return RedirectResponse(url="/admin/board", status_code=303)    

# [POST] 게시판 설정 수정 처리
@app.post("/admin/board/update")
async def update_board(
    board_id: str = Form(...),
    name: str = Form(...),
    type: str = Form(...),
    auth: str = Form(...),
    user=Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    global boards
    for b in boards:
        if b['id'] == board_id:
            b['name'] = name
            b['type'] = type
            b['auth'] = auth
            break
            
    return RedirectResponse(url="/admin/board", status_code=303)

# [GET] 게시판 삭제 처리
@app.get("/admin/board/delete/{board_id}")
async def delete_board(board_id: str, user=Depends(get_current_user)):
    if not user: return RedirectResponse(url="/", status_code=303)
    
    global boards
    boards = [b for b in boards if b['id'] != board_id]
    return RedirectResponse(url="/admin/board", status_code=303)