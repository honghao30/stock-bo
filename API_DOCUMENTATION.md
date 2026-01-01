# REST API 문서

## 기본 정보
- Base URL: `http://your-domain.com`
- Content-Type: `application/json`
- Response Format: JSON
- **인증**: JWT Bearer 토큰 필수 (모든 API 엔드포인트)

## 인증 (Authentication)

모든 API 엔드포인트는 인증이 필요합니다. JWT Bearer 토큰을 사용합니다.

### 1. 토큰 발급 (로그인)

**POST** `/api/auth/login`

**요청 본문:**
```json
{
  "username": "admin@example.com",
  "password": "your-password"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**에러 응답 (401):**
```json
{
  "detail": "아이디 또는 비밀번호가 잘못되었습니다"
}
```

### 2. API 호출 시 토큰 사용

발급받은 토큰을 HTTP 헤더에 포함하여 요청합니다:

```
Authorization: Bearer <access_token>
```

**예시:**
```javascript
fetch('http://your-domain.com/api/boards', {
  headers: {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
  }
})
```

**에러 응답 (401):**
```json
{
  "detail": "유효하지 않은 토큰입니다"
}
```

**토큰 만료 시간**: 24시간

---

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

**인증**: Bearer 토큰 필수

**헤더:**
```
Authorization: Bearer <token>
```

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

**인증**: Bearer 토큰 필수

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

**인증**: Bearer 토큰 필수

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

**인증**: Bearer 토큰 필수

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

**인증**: Bearer 토큰 필수

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

**인증**: Bearer 토큰 필수

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

#### 1. 로그인 및 토큰 발급
```javascript
// 로그인
async function login(username, password) {
  const response = await fetch('http://your-domain.com/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  if (response.ok) {
    const data = await response.json();
    // 토큰을 localStorage에 저장
    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  } else {
    throw new Error('로그인 실패');
  }
}

// 로그인 실행
const token = await login('admin@example.com', 'password123');
```

#### 2. 인증된 API 호출
```javascript
// 토큰 가져오기
const token = localStorage.getItem('access_token');

// 게시판 목록 조회
fetch('http://your-domain.com/api/boards', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => {
    console.log(data.data); // 게시판 목록
  });

// 게시글 목록 조회 (페이지네이션)
fetch('http://your-domain.com/api/boards/B001/posts?page=1&limit=10', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => {
    console.log(data.data); // 게시글 목록
    console.log(data.pagination); // 페이지네이션 정보
  });

// 일정 목록 조회 (날짜 필터)
fetch('http://your-domain.com/api/schedules?start_date=2024-01-01&end_date=2024-12-31', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => {
    console.log(data.data); // 일정 목록
  });
```

#### 3. axios 사용 예시 (권장)
```javascript
import axios from 'axios';

const API_BASE_URL = 'http://your-domain.com';

// axios 인스턴스 생성 (토큰 자동 포함)
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 요청 인터셉터: 모든 요청에 토큰 자동 추가
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 로그인
const loginResponse = await apiClient.post('/api/auth/login', {
  username: 'admin@example.com',
  password: 'password123'
});
localStorage.setItem('access_token', loginResponse.data.access_token);

// API 호출 (토큰 자동 포함됨)
const boardsResponse = await apiClient.get('/api/boards');
console.log(boardsResponse.data.data);
```

### Python (requests)
```python
import requests

API_BASE_URL = 'http://your-domain.com'

# 1. 로그인 및 토큰 발급
login_response = requests.post(
    f'{API_BASE_URL}/api/auth/login',
    json={
        'username': 'admin@example.com',
        'password': 'password123'
    }
)
login_data = login_response.json()
access_token = login_data['access_token']

# 헤더에 토큰 포함
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# 2. 게시판 목록 조회
response = requests.get(
    f'{API_BASE_URL}/api/boards',
    headers=headers
)
data = response.json()
print(data['data'])

# 3. 게시글 목록 조회
response = requests.get(
    f'{API_BASE_URL}/api/boards/B001/posts',
    headers=headers,
    params={
        'page': 1,
        'limit': 10
    }
)
data = response.json()
print(data['data'])
print(data['pagination'])

# 4. 일정 목록 조회
response = requests.get(
    f'{API_BASE_URL}/api/schedules',
    headers=headers,
    params={
        'start_date': '2024-01-01',
        'end_date': '2024-12-31'
    }
)
data = response.json()
print(data['data'])
```

---

## 에러 코드

- `400`: 잘못된 요청 (예: 잘못된 날짜 형식)
- `401`: 인증 실패 (토큰이 없거나 유효하지 않음)
  ```json
  {
    "detail": "유효하지 않은 토큰입니다"
  }
  ```
- `404`: 리소스를 찾을 수 없음
- `500`: 서버 내부 오류

## 보안 주의사항

1. **토큰 보안**: 발급받은 토큰은 안전하게 보관하세요. 클라이언트 측에서는 localStorage나 안전한 스토리지에 저장하세요.
2. **HTTPS 사용**: 프로덕션 환경에서는 반드시 HTTPS를 사용하세요.
3. **토큰 만료**: 토큰은 24시간 후 만료됩니다. 만료 시 다시 로그인하여 새 토큰을 발급받으세요.
4. **환경 변수 설정**: `.env` 파일에 `JWT_SECRET_KEY`를 안전한 값으로 설정하세요.

