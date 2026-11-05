# Mini Project Vibe API

FastAPI와 Supabase PostgreSQL로 만든 팀 프로젝트 백엔드입니다. User, Post, Comment, Support CRUD와 Gemini Chat API를 제공합니다.

## 기술 스택

- Python 3.12.7
- FastAPI / Pydantic v2
- Supabase PostgreSQL
- Google Gen AI SDK
- pytest
- Render

## API

| 기능 | Method | Path |
|---|---|---|
| Health | GET | `/health` |
| User 생성 | POST | `/users` |
| User 전체 조회 | GET | `/users` |
| User 단일 조회 | GET | `/users/{user_id}` |
| User 수정 | PUT | `/users/{user_id}` |
| User 삭제 | DELETE | `/users/{user_id}` |
| Post 생성/목록 | POST/GET | `/posts` |
| Post 조회/수정/삭제 | GET/PUT/DELETE | `/posts/{post_id}` |
| Comment 생성 | POST | `/posts/{post_id}/comments` |
| Comment 전체 조회 | GET | `/comments` |
| Post Comment 조회 | GET | `/posts/{post_id}/comments` |
| Comment 조회/수정/삭제 | GET/PUT/DELETE | `/comments/{comment_id}` |
| Support 생성/목록 | POST/GET | `/supports` |
| Support 조회/수정/삭제 | GET/PUT/DELETE | `/supports/{support_id}` |
| Gemini Chat | POST | `/chat/gemini` |

## 로컬 실행

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에 실제 값을 직접 입력합니다. 실제 키를 Git에 추가하지 마세요.

```powershell
uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- Health Check: <http://127.0.0.1:8000/health>

## Supabase SQL

Supabase SQL Editor에서 다음 순서로 실행합니다.

1. `sql/user.sql`
2. `sql/post.sql`
3. `sql/comment.sql`
4. `sql/support.sql`
5. 개발 환경에서만 `sql/seed.sql`

샘플 데이터 삭제:

```text
sql/cleanup_seed.sql
```

## 테스트

테스트는 실제 Supabase와 Gemini를 호출하지 않습니다.

```powershell
python -m pytest -q
```

## Render 배포

저장소의 `render.yaml`을 Blueprint로 사용하거나 다음 값을 Web Service에 직접 입력합니다.

- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Render Environment Variables:

```text
PYTHON_VERSION=3.12.7
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash
```

실제 비밀값은 Render Dashboard에만 입력합니다.

## 개발 문서

- [사전 계획](pre_plan.md)
- [바이브 코딩 가이드](vibe_coding.md)

## 보안 원칙

- 공개 응답에 비밀번호를 포함하지 않습니다.
- 비밀번호는 PBKDF2-HMAC-SHA256으로 해시합니다.
- DB와 Gemini 내부 오류를 API 응답에 그대로 노출하지 않습니다.
- `.env`와 실제 키를 Git에 올리지 않습니다.
- Service Role Key는 서버 환경에서만 사용합니다.
