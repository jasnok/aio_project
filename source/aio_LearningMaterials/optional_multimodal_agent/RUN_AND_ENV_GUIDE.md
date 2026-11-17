# 실행 및 환경변수 작성 안내

## 1. 사용자가 입력해야 하는 값

다음 두 파일의 `OPENAI_API_KEY=` 뒤에 본인의 키를 입력합니다.

- `backend/.env`
- `mcp_server/.env`

Docker로 실행할 때는 다음 두 파일에도 같은 방식으로 입력합니다.

- `backend/.env.docker`
- `mcp_server/.env.docker`

`.env`와 `.env.docker`는 `.gitignore`에 포함되어 있으므로 저장소에 커밋하지 않습니다.
Frontend에는 비밀값이 필요하지 않습니다.

Release Compose를 사용할 경우 프로젝트 루트의 PowerShell 환경변수에 다음 이미지명을 지정합니다. 프로젝트 루트에는 `.env`를 만들지 않습니다.

```dotenv
BACKEND_IMAGE=ghcr.io/YOUR_ACCOUNT/optional-multimodal-agent-backend:latest
FRONTEND_IMAGE=ghcr.io/YOUR_ACCOUNT/optional-multimodal-agent-frontend:latest
MCP_SERVER_IMAGE=ghcr.io/YOUR_ACCOUNT/optional-multimodal-agent-mcp-server:latest
```

`YOUR_ACCOUNT`와 태그는 실제 Registry 정보로 바꿉니다.

## 2. 로컬 실행

각 서비스는 자신의 가상환경과 `.env`를 사용합니다.

```powershell
cd C:\optional_multimodal_agent\mcp_server
.\.venv\Scripts\python.exe main.py
```

```powershell
cd C:\optional_multimodal_agent\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

```powershell
cd C:\optional_multimodal_agent\backend
.\.venv\Scripts\python.exe workers\agent_worker.py
```

```powershell
cd C:\optional_multimodal_agent\frontend
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 3. 서비스별 테스트

```powershell
cd C:\optional_multimodal_agent\backend
.\.venv\Scripts\python.exe -m pytest -q

cd C:\optional_multimodal_agent\frontend
.\.venv\Scripts\python.exe -m pytest -q

cd C:\optional_multimodal_agent\mcp_server
.\.venv\Scripts\python.exe -m pytest -q
```

## 4. Docker Compose 실행

개발용 이미지를 빌드하고 실행합니다.

```powershell
cd C:\optional_multimodal_agent
docker compose -f compose.yml up -d --build
docker compose -f compose.yml ps
```

로그 확인:

```powershell
docker compose -f compose.yml logs -f
```

종료:

```powershell
docker compose -f compose.yml down
```

DB 및 미디어 볼륨까지 삭제하는 `down -v`는 데이터를 지우므로 사용하지 않습니다.

Release 이미지 실행:

```powershell
$env:BACKEND_IMAGE="ghcr.io/YOUR_ACCOUNT/optional-multimodal-agent-backend:latest"
$env:FRONTEND_IMAGE="ghcr.io/YOUR_ACCOUNT/optional-multimodal-agent-frontend:latest"
$env:MCP_SERVER_IMAGE="ghcr.io/YOUR_ACCOUNT/optional-multimodal-agent-mcp-server:latest"
docker compose -f compose.release.yml up -d
```

## 5. PostgreSQL과 RAG 데이터 다시 준비하기

현재 PostgreSQL 컨테이너는 `aidevs-pgvector`, 이미지는 `pgvector/pgvector:pg16`, 호스트 포트는 `5433`, 볼륨은 `aidevs-pgvector-data`입니다. 기존 볼륨의 초기 설정인 `agent_db`, `agent_user`, `agent_pwd`를 그대로 사용합니다.

```powershell
docker start aidevs-pgvector
docker start aidevs-redis
docker start aidevs-ollama
```

테이블과 업무 데이터를 다시 적용할 때:

```powershell
cd C:\optional_multimodal_agent
.\mcp_server\.venv\Scripts\python.exe -m scripts.setup_database
.\mcp_server\.venv\Scripts\python.exe -m scripts.seed_database
```

RAG 문서를 다시 적재할 때:

```powershell
.\mcp_server\.venv\Scripts\python.exe -m scripts.ingest_knowledge
```

## 6. 접속 주소

- Frontend: http://127.0.0.1:8501
- Backend API 문서: http://127.0.0.1:8000/docs
- Backend 상태: http://127.0.0.1:8000/health
- MCP Server: http://127.0.0.1:8020/mcp
- PostgreSQL: `127.0.0.1:5433`

## 7. PostgreSQL 이미지 확인 결과

현재 사용 중인 이미지는 `pgvector/pgvector:pg16`입니다. 기존 `aidevs-pgvector-data` 볼륨과 PostgreSQL major version이 같아 그대로 재사용할 수 있습니다. 현재 확인된 버전은 PostgreSQL 16.15, pgvector 0.8.6입니다.
