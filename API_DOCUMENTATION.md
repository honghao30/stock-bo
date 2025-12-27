# REST API 문서

## 기본 정보
- Base URL: `http://your-domain.com`
- Content-Type: `application/json`
- Response Format: JSON

## 응답 형식

### 성공 응답
```json
{
  "success": true,
  "data": { ... },
  "count": 10  // 목록 조회 시
}
```

### 에러 응답
```json
{
  "detail": "에러 메시지"
}
```

---

## 게시판 API

### 1. 게시판 목록 조회
**GET** `/api/boards`

**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "id": "B001",
      "name": "자유게시판",
      "type": "korean",
      "auth": "all",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "post_count": 10
    }
  ],
  "count": 1
}
```

### 2. 게시판 상세 조회
**GET** `/api/boards/{board_id}`

**파라미터:**
- `board_id` (path): 게시판 ID (예: "B001")

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "id": "B001",
    "name": "자유게시판",
    "type": "korean",
    "auth": "all",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "post_count": 10
  }
}
```

### 3. 게시판의 게시글 목록 조회
**GET** `/api/boards/{board_id}/posts`

**파라미터:**
- `board_id` (path): 게시판 ID
- `page` (query, optional): 페이지 번호 (기본값: 1)
- `limit` (query, optional): 페이지당 항목 수 (기본값: 10, 최대: 100)

**예시:**
```
GET /api/boards/B001/posts?page=1&limit=10
```

**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "board_id": "B001",
      "title": "게시글 제목",
      "content": "게시글 내용 (HTML)",
      "author": "admin@example.com",
      "views": 10,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "attachments": [
        {
          "filename": "file.pdf",
          "path": "/uploads/files/20240101_file.pdf",
          "size": 1024,
          "type": "application/pdf"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total_count": 50,
    "total_pages": 5
  }
}
```

### 4. 게시글 상세 조회
**GET** `/api/posts/{post_id}`

**파라미터:**
- `post_id` (path): 게시글 ID

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "board_id": "B001",
    "board": {
      "id": "B001",
      "name": "자유게시판",
      "type": "korean"
    },
    "title": "게시글 제목",
    "content": "게시글 내용 (HTML)",
    "author": "admin@example.com",
    "views": 11,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "attachments": []
  }
}
```

**참고:** 이 API를 호출하면 조회수가 자동으로 증가합니다.

---

## 일정 관리 API

### 1. 일정 목록 조회
**GET** `/api/schedules`

**쿼리 파라미터:**
- `start_date` (optional): 시작 날짜 (YYYY-MM-DD 형식)
- `end_date` (optional): 종료 날짜 (YYYY-MM-DD 형식)
- `type` (optional): 일정 타입 ("manual" 또는 "api")

**예시:**
```
GET /api/schedules?start_date=2024-01-01&end_date=2024-12-31&type=manual
```

**응답 예시:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "date": "2024-01-15",
      "subject": "회의 일정",
      "content": "오후 2시 회의실",
      "type": "manual",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "count": 1
}
```

### 2. 일정 상세 조회
**GET** `/api/schedules/{schedule_id}`

**파라미터:**
- `schedule_id` (path): 일정 ID

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "date": "2024-01-15",
    "subject": "회의 일정",
    "content": "오후 2시 회의실",
    "type": "manual",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

---

## 사용 예시

### JavaScript (Fetch API)
```javascript
// 게시판 목록 조회
fetch('http://your-domain.com/api/boards')
  .then(response => response.json())
  .then(data => {
    console.log(data.data); // 게시판 목록
  });

// 게시글 목록 조회 (페이지네이션)
fetch('http://your-domain.com/api/boards/B001/posts?page=1&limit=10')
  .then(response => response.json())
  .then(data => {
    console.log(data.data); // 게시글 목록
    console.log(data.pagination); // 페이지네이션 정보
  });

// 일정 목록 조회 (날짜 필터)
fetch('http://your-domain.com/api/schedules?start_date=2024-01-01&end_date=2024-12-31')
  .then(response => response.json())
  .then(data => {
    console.log(data.data); // 일정 목록
  });
```

### Python (requests)
```python
import requests

# 게시판 목록 조회
response = requests.get('http://your-domain.com/api/boards')
data = response.json()
print(data['data'])

# 게시글 목록 조회
response = requests.get('http://your-domain.com/api/boards/B001/posts', params={
    'page': 1,
    'limit': 10
})
data = response.json()
print(data['data'])
print(data['pagination'])
```

---

## 에러 코드

- `400`: 잘못된 요청 (예: 잘못된 날짜 형식)
- `404`: 리소스를 찾을 수 없음
- `500`: 서버 내부 오류

