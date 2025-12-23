import os
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

# .env 파일 로드
load_dotenv()

app = FastAPI()

# os.environ.get을 통해 환경 변수에서 값을 가져옵니다.
# 값이 없을 경우를 대비해 기본값을 설정할 수도 있습니다.
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PW = os.environ.get("ADMIN_PW")
AUTH_COOKIE_NAME = os.environ.get("AUTH_COOKIE_NAME")
SECRET_TOKEN = os.environ.get("SECRET_TOKEN")

# 2. 인증 확인 함수
async def get_current_user(request: Request):
    session_id = request.cookies.get(AUTH_COOKIE_NAME)
    if session_id != SECRET_TOKEN:
        return None
    return session_id

# 3. [GET] / : 초기 접속 화면 (인증 필요 안내)
@app.get("/", response_class=HTMLResponse)
async def read_root(user=Depends(get_current_user)):
    # 이미 로그인된 사용자가 루트로 오면 대시보드로 바로 보냄
    if user:
        return RedirectResponse(url="/admin/dashboard")
        
    return """
    <div style="text-align:center; padding:100px; font-family:sans-serif;">
        <h1 style="color:#e74c3c;">🛑 관리자 인증 필요</h1>
        <p style="font-size:18px; color:#555;">허가되지 않은 접근입니다. 로그인 후 이용해주세요.</p>
        <br>
        <a href="/login" style="padding:15px 30px; background:#3498db; color:white; text-decoration:none; border-radius:8px; font-weight:bold; transition: 0.3s;">
            로그인 페이지로 이동
        </a>
    </div>
    """

# 4. [GET] /login : 로그인 화면 출력
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
            <button type="submit" style="padding: 12px; background: #2c3e50; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">로그인</button>
        </form>
    </div>
    """

# 5. [POST] /login : 로그인 처리
@app.post("/login")
async def do_login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_EMAIL and password == ADMIN_PW:
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(key=AUTH_COOKIE_NAME, value=SECRET_TOKEN, httponly=True)
        return response
    return HTMLResponse("<script>alert('정보가 일치하지 않습니다.'); window.location.href='/login';</script>")

# 6. [GET] /admin/dashboard : 관리자 전용 페이지
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(user=Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/") # 인증 없으면 루트 경고창으로 보냄
        
    return f"""
    <div style="padding: 50px; font-family: sans-serif;">
        <h1 style="color: #2c3e50;">🚀 BO 관리자 시스템</h1>
        <p>환영합니다, <b>{ADMIN_EMAIL}</b> 관리자님.</p>
        <hr>
        <div style="margin-top: 30px;">
            <button onclick="location.href='/api/fetch-data'" style="padding: 10px 20px;">외부 API 데이터 수집</button>
            <button onclick="location.href='/logout'" style="padding: 10px 20px; background: #e74c3c; color: white; border: none; border-radius: 4px; margin-left: 10px;">로그아웃</button>
        </div>
    </div>
    """

# 7. [GET] /logout : 로그아웃
@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response