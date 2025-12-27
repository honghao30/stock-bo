"""
게시판 관리 라우터
"""
import os
import json
import re
from fastapi import APIRouter, Form, Request, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.dependencies import get_current_user
from app.config import ADMIN_EMAIL
from app.database import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def format_file_size(bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형식으로 변환"""
    if not bytes or bytes == 0:
        return '0 Bytes'
    k = 1024
    sizes = ['Bytes', 'KB', 'MB', 'GB']
    i = int(bytes.bit_length() / 10) if bytes > 0 else 0
    i = min(i, len(sizes) - 1)
    return f"{round(bytes / (k ** i) * 100) / 100} {sizes[i]}"


def parse_attached_files(content: str) -> List[dict]:
    """content에서 첨부파일 정보를 파싱하여 반환"""
    if not content:
        return []
    
    files = []
    # HTML 주석에서 첨부 파일 정보 추출
    pattern = r'<!--\s*ATTACHED_FILES:\s*(\[[\s\S]*?\])\s*-->'
    match = re.search(pattern, content)
    
    if match:
        try:
            files = json.loads(match.group(1))
            # 파일 크기 포맷팅 추가
            for file in files:
                if 'size' in file and file['size']:
                    file['formatted_size'] = format_file_size(file['size'])
        except (json.JSONDecodeError, Exception) as e:
            print(f"첨부파일 파싱 오류: {e}")
            return []
    
    return files if isinstance(files, list) else []

# =========================================================
# [관리자용] 게시판 관리 기능
# =========================================================

@router.get("/admin/board", response_class=HTMLResponse)
async def admin_board_page(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    boards = db.query(models.Board).order_by(models.Board.created_at).all()
    return templates.TemplateResponse("board_admin.html", {
        "request": request, "admin_email": ADMIN_EMAIL, "boards": boards, "active_page": "board"
    })

@router.post("/admin/board/create")
async def create_board(name: str = Form(...), type: str = Form(...), auth: str = Form(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    try:
        cnt = db.query(models.Board).count()
        new_id = f"B{cnt + 1:03d}"
        while db.query(models.Board).filter(models.Board.id == new_id).first():
            cnt += 1
            new_id = f"B{cnt + 1:03d}"
        
        db.add(models.Board(id=new_id, name=name, type=type, auth=auth))
        db.commit()
        return RedirectResponse(url="/admin/board", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/board/update")
async def update_board(board_id: str = Form(...), name: str = Form(...), type: str = Form(...), auth: str = Form(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board:
        board.name = name
        board.type = type
        board.auth = auth
        db.commit()
    return RedirectResponse(url="/admin/board", status_code=303)

@router.get("/admin/board/delete/{board_id}")
async def delete_board(board_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/", status_code=303)
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if board:
        db.delete(board)
        db.commit()
    return RedirectResponse(url="/admin/board", status_code=303)

@router.get("/admin/board/{board_id}/posts", response_class=HTMLResponse)
async def admin_board_posts_page(board_id: str, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board: raise HTTPException(status_code=404)
    posts = db.query(models.Post).filter(models.Post.board_id == board_id).order_by(models.Post.created_at.desc()).all()
    return templates.TemplateResponse("admin_board_posts.html", {
        "request": request, "admin_email": ADMIN_EMAIL, "board": board, "posts": posts, "active_page": "board"
    })

@router.get("/admin/board/{board_id}/write", response_class=HTMLResponse)
async def admin_write_post_page(board_id: str, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    return templates.TemplateResponse("admin_post_write.html", {
        "request": request, 
        "board": board, 
        "admin_email": ADMIN_EMAIL, 
        "active_page": "board"
    })

@router.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """에디터 이미지 업로드"""
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    # 이미지 파일만 허용
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    # 파일 크기 체크 (5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기는 5MB 이하여야 합니다.")
    
    try:
        # uploads/images 디렉토리 생성
        upload_dir = "uploads/images"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ") if file.filename else "image"
        safe_filename = f"{timestamp}_{safe_name}"
        file_path = os.path.join(upload_dir, safe_filename)
        
        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # URL 반환
        from fastapi.responses import JSONResponse
        return JSONResponse({"url": f"/uploads/images/{safe_filename}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 업로드 실패: {str(e)}")


@router.post("/admin/board/{board_id}/write")
async def admin_create_post(
    board_id: str,
    title: str = Form(...),
    content: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """게시글 작성 (파일 첨부 포함)"""
    if not user:
        return RedirectResponse(url="/")
    
    try:
        # 게시글 저장
        new_post = models.Post(
            board_id=board_id,
            title=title.strip(),
            content=content,
            author=ADMIN_EMAIL,
            created_at=datetime.now()
        )
        db.add(new_post)
        db.flush()  # post.id를 얻기 위해 flush
        
        # 파일 저장
        uploaded_files = []
        if files:
            # uploads/files 디렉토리 생성
            upload_dir = "uploads/files"
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in files:
                if file and file.filename:
                    # 파일명 중복 방지를 위해 타임스탬프 추가
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    # 파일명에서 특수문자 제거
                    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
                    safe_filename = f"{timestamp}_{safe_name}"
                    file_path = os.path.join(upload_dir, safe_filename)
                    
                    # 파일 저장
                    try:
                        with open(file_path, "wb") as f:
                            content_data = await file.read()
                            f.write(content_data)
                        
                        # 파일 정보 저장
                        file_info = {
                            "filename": file.filename,
                            "path": f"/uploads/files/{safe_filename}",
                            "size": len(content_data),
                            "type": file.content_type or "application/octet-stream"
                        }
                        uploaded_files.append(file_info)
                    except Exception as e:
                        print(f"파일 저장 실패: {file.filename}, 오류: {e}")
                        continue
            
            # 첨부 파일 정보를 content에 HTML 주석으로 추가
            if uploaded_files:
                import json
                files_html = f'<!-- ATTACHED_FILES:{json.dumps(uploaded_files, ensure_ascii=False)} -->'
                content = content + files_html
        
        db.commit()
        return RedirectResponse(url=f"/admin/board/{board_id}/posts", status_code=303)
    except Exception as e:
        db.rollback()
        print(f"게시글 작성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"게시글 작성 중 오류가 발생했습니다: {str(e)}")

@router.get("/admin/board/{board_id}/post/{post_id}", response_class=HTMLResponse)
async def admin_post_view(board_id: str, post_id: int, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not user: return RedirectResponse(url="/")
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    return templates.TemplateResponse("admin_post_view.html", {
        "request": request, 
        "board": {"id": board_id}, 
        "post": post, 
        "admin_email": ADMIN_EMAIL, 
        "active_page": "board"
    })


# =========================================================
# [사용자용] 게시판 & 방명록 (핵심 로직 수정됨)
# =========================================================

@router.get("/boards", response_class=HTMLResponse)
async def board_list_page(request: Request, db: Session = Depends(get_db)):
    """게시판 목록 (메인)"""
    boards = db.query(models.Board).order_by(models.Board.created_at).all()
    return templates.TemplateResponse("board_list.html", {"request": request, "boards": boards})


@router.get("/board/{board_id}", response_class=HTMLResponse)
async def board_detail_page(
    board_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    게시판 상세 화면 (목록)
    - 방명록형: [입력폼] -> [최신글 내용 목록] (board_detail.html에서 처리)
    - 일반형: [글쓰기 버튼] -> [제목 목록] (board_detail.html에서 처리)
    """
    # 1. 게시판 정보 조회
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="게시판을 찾을 수 없습니다.")
    
    # 2. 게시글 목록 조회 (최신순 정렬: created_at desc)
    posts = db.query(models.Post).filter(
        models.Post.board_id == board_id
    ).order_by(models.Post.created_at.desc()).all()
    
    # 각 게시글의 첨부파일 정보 파싱
    posts_with_attachments = []
    for post in posts:
        attachments = parse_attached_files(post.content or "")
        posts_with_attachments.append({
            "post": post,
            "attachments": attachments
        })
    
    return templates.TemplateResponse("board_detail.html", {
        "request": request,
        "board": board,
        "posts_with_attachments": posts_with_attachments,
    })


@router.post("/board/write")
async def public_create_post(
    board_id: str = Form(...),
    writer: str = Form(...),          # 작성자 이름
    content: str = Form(...),         # 내용
    password: str = Form(None),       # 비밀번호 (선택)
    title: str = Form(None),          # 제목 (방명록은 없을 수 있음)
    db: Session = Depends(get_db)
):
    """
    사용자 글쓰기 처리 (일반글 & 방명록 공통)
    """
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    # 제목 처리: 방명록은 제목이 없으므로 자동 생성
    final_title = title
    if not final_title:
        if board.type in ["guestbook", "guest"]:
            # 내용의 앞 20자를 제목으로 사용
            final_title = content[:20] + "..." if len(content) > 20 else content
        else:
            final_title = "무제"

    # DB 저장
    new_post = models.Post(
        board_id=board_id,
        title=final_title,
        content=content,
        author=writer,
        created_at=datetime.now() # 현재 시간 저장
    )
    
    db.add(new_post)
    db.commit()
    
    # 작성 후 다시 해당 게시판 페이지로 이동 (방명록은 리스트로, 일반형도 리스트로)
    return RedirectResponse(url=f"/board/{board_id}", status_code=303)


# [일반 게시판 전용] 글쓰기 페이지 (방명록은 사용 안 함)
@router.get("/board/{board_id}/write", response_class=HTMLResponse)
async def public_write_page_view(board_id: str, request: Request, db: Session = Depends(get_db)):
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board: raise HTTPException(status_code=404)
    return templates.TemplateResponse("post_write_public.html", {"request": request, "board": board})


# [일반 게시판 전용] 상세 보기 페이지 (방명록은 사용 안 함)
@router.get("/board/{board_id}/post/{post_id}", response_class=HTMLResponse)
async def public_post_view_page(
    board_id: str, 
    post_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    # 1. 게시판 정보 조회 (이전 코드에서 누락되어 에러 발생했던 부분 해결)
    board = db.query(models.Board).filter(models.Board.id == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="게시판 없음")

    # 2. 게시글 정보 조회
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post: 
        raise HTTPException(status_code=404, detail="게시글 없음")
    
    # 3. 조회수 증가
    post.views = (post.views or 0) + 1
    db.commit()
    
    # 4. 첨부파일 정보 파싱
    attachments = parse_attached_files(post.content or "")
    
    # 5. 템플릿에 board와 post 모두 전달
    return templates.TemplateResponse("post_view.html", {
        "request": request, 
        "board": board, 
        "post": post,
        "attachments": attachments
    })