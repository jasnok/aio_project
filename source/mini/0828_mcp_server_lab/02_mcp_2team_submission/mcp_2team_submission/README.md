# Tour & Weather MCP 로컬 통합 프로젝트

Frontend, Backend, Tour MCP, Weather MCP와 Docker pgvector DB를 한 컴퓨터에서 실행하는 프로젝트입니다. 두 MCP 서버는 stdio가 아닌 Streamable HTTP로 연결됩니다.

## 전체 구성

```text
Browser
  └─ Frontend Streamlit :8501
       └─ Backend FastAPI :8000
            ├─ Tour MCP :8020 ── pgvector DB :5432
            │                    └─ Ollama embedding :11435
            └─ Weather MCP :8013 ── 기상청 API
```

현재 확인된 이 컴퓨터의 LAN IPv4는 `192.100.200.232`입니다. 서버는 IP 변경에 유연하도록 `0.0.0.0`에 바인딩하고, 서비스 간 접속 URL에는 LAN IP를 사용합니다.

| 서비스 | 로컬/LAN 주소 |
| --- | --- |
| Frontend | `http://192.100.200.232:8501` |
| Backend | `http://192.100.200.232:8000` |
| Tour MCP | `http://192.100.200.232:8020/mcp` |
| Weather MCP | `http://192.100.200.232:8013/mcp` |
| pgvector | `192.100.200.232:5432` |
| 프로젝트 Ollama | `http://192.100.200.232:11435` |

IP가 바뀌면 `app/tour/.env`, `backend/.env`, `frontend/.env`의 URL 또는 DB 주소와 `run/check_all.ps1`의 기본 `HostIp`를 새 IP로 변경합니다.

## 폴더 구조

```text
├─ app/
│  ├─ tour/                 # Tour Streamable HTTP MCP
│  │  ├─ main.py
│  │  ├─ core/
│  │  ├─ database/
│  │  ├─ rag/
│  │  ├─ repositories/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ tests/
│  │  └─ tools/
│  └─ weather/              # Weather Streamable HTTP MCP
│     ├─ main.py
│     ├─ core/
│     ├─ external_clients/
│     ├─ schemas/
│     ├─ services/
│     ├─ tests/
│     └─ tools/
├─ backend/                 # FastAPI와 MCP Agent
├─ frontend/                # Streamlit UI
├─ resources/
│  ├─ database/
│  │  ├─ docker-compose.yml
│  │  ├─ populate_tour_documents.py
│  │  └─ sql/
│  ├─ data/
│  └─ docs/
├─ run/
│  ├─ start_all.ps1
│  ├─ stop_all.ps1
│  ├─ check_all.ps1
│  ├─ run_tests.ps1
│  └─ check_mcp_http.py
├─ README.md
└─ requirements.txt
```

## 사전 요구사항

- Python 3.11 이상
- Docker Desktop
- PowerShell
- OpenAI API Key: Backend Agent에 필요하며, 선택하면 Tour 임베딩에도 사용
- 기상청 API Key: 현재 날씨 조회에 필요

Tour 임베딩은 기본적으로 로컬 Docker Ollama를 사용하므로 API 키가 없어도 호텔·관광지·호텔 정책 벡터 검색을 실행할 수 있습니다. OpenAI Agent의 자연어 최종 답변과 실제 기상청 날씨 응답에는 각 API 키가 필요합니다.

## 설치

프로젝트 루트에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

예시 환경변수 파일로 처음 구성하는 경우:

```powershell
Copy-Item .\resources\database\.env.example .\resources\database\.env
Copy-Item .\app\tour\.env.example .\app\tour\.env
Copy-Item .\app\weather\.env.example .\app\weather\.env
Copy-Item .\backend\.env.example .\backend\.env
Copy-Item .\frontend\.env.example .\frontend\.env
```

`.env` 파일은 Git에 포함되지 않습니다. DB 비밀번호는 `resources/database/.env`와 `app/tour/.env`의 `DATABASE_URL`에서 동일해야 합니다.

## 필수 환경변수

`app/tour/.env`:

```dotenv
TOUR_MCP_HOST=0.0.0.0
TOUR_MCP_PORT=8020
DATABASE_URL=postgresql://사용자:비밀번호@192.100.200.232:5432/travel_mcp
TOUR_EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.100.200.232:11435
OLLAMA_EMBEDDING_MODEL=embeddinggemma
OPENAI_API_KEY=
```

`app/weather/.env`:

```dotenv
MCP_HOST=0.0.0.0
MCP_PORT=8013
KMA_API_KEY=실제키
KMA_API_BASE_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
KMA_API_VERSION=2.0
```

`backend/.env`:

```dotenv
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
TOUR_MCP_URL=http://192.100.200.232:8020/mcp
WEATHER_MCP_URL=http://192.100.200.232:8013/mcp
OPENAI_API_KEY=실제키
```

`frontend/.env`:

```dotenv
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=8501
BACKEND_API_URL=http://192.100.200.232:8000
```

## 전체 서버 한 번에 실행

Docker Desktop을 실행한 상태에서 프로젝트 루트에서 실행합니다.

```powershell
.\run\start_all.ps1
```

실행 순서:

1. pgvector와 프로젝트 전용 Ollama Docker 컨테이너 시작 및 healthcheck
2. Tour MCP 시작
3. Weather MCP 시작
4. Backend 시작
5. Frontend 시작

최초 한 번은 Ollama 임베딩 모델과 DB 검색 문서를 준비합니다.

```powershell
.\run\setup_ollama.ps1
.\run\migrate_database.ps1
python .\resources\database\populate_tour_documents.py
```

백그라운드 로그는 `logs/`에 저장됩니다.

## 전체 상태 확인

```powershell
.\run\check_all.ps1
```

IP가 변경된 경우:

```powershell
.\run\check_all.ps1 -HostIp "새로운_IP"
```

검사 항목:

- pgvector 컨테이너 health
- vector 확장
- 호텔·관광지·호텔 정책·검색 문서 건수
- Ollama health와 `embeddinggemma` 설치 여부
- Tour/Weather MCP Tool discovery
- 부산 12만 원 이하 호텔 검색 → 검색된 호텔 ID의 당일 취소 정책 RAG
- Backend health
- Backend에서 두 MCP 서버 연결
- Frontend HTTP 200

## 전체 서버 종료

```powershell
.\run\stop_all.ps1
```

애플리케이션 프로세스와 DB 컨테이너를 중지하지만 pgvector Docker volume은 삭제하지 않으므로 DB 데이터는 보존됩니다.

## 개별 실행

DB:

```powershell
docker compose --env-file .\resources\database\.env `
  -f .\resources\database\docker-compose.yml up -d
```

Tour MCP:

```powershell
python -m app.tour.main
```

Weather MCP:

```powershell
python -m app.weather.main
```

Backend:

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
python -m streamlit run frontend\app.py `
  --server.address 0.0.0.0 --server.port 8501
```

## 테스트

문법과 Tour·Weather 단위 테스트:

```powershell
.\run\run_tests.ps1
```

실행 중인 두 MCP 서버까지 확인:

```powershell
.\run\run_tests.ps1 -Integration
```

## DB와 SQL

pgvector volume을 처음 생성할 때 다음 SQL이 번호 순서대로 자동 실행됩니다.

```text
001_hotels.sql
002_attractions.sql
003_tour_documents.sql
004_hotel_policies.sql
```

현재 기본 데이터는 호텔 200건, 관광지 100건, 검증용 가상 호텔 정책 600건입니다. 정책은 실제 호텔 약관이 아니므로 사용자 답변에 데모 데이터임을 명시합니다. `tour_documents`는 선택한 임베딩 Provider로 별도 적재합니다.

```powershell
python .\resources\database\populate_tour_documents.py
```

기본 `ollama` 설정은 로컬 `embeddinggemma`를 사용해 API 비용이 없습니다. OpenAI로 바꾸려면 `app/tour/.env`에서 다음처럼 변경한 뒤 같은 적재 명령을 실행합니다.

```dotenv
TOUR_EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=실제키
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=1536
```

Provider·모델·차원은 문서별로 함께 저장되므로 Ollama와 OpenAI 임베딩을 같은 DB에 보관할 수 있고, 검색 시 현재 선택한 설정의 문서만 사용합니다.

## 목표 질문 처리 흐름

```text
“부산으로 2일 여행을 가려고 해. 120000원 이하 호텔을 검색해 줘.
 오늘 날씨 알려줘. 당일 취소에 대해 알려줘.”
```

Backend Agent는 다음 순서를 따릅니다.

1. Tour `search_hotels`: 부산, 1박 120,000원 이하 호텔 검색
2. Weather `get_current_weather`: 부산 오늘 날씨 조회
3. Tour `search_hotel_policies`: 1번 결과의 `hotel_id`만 넘겨 당일 취소 규정 검색
4. 검색 결과를 합쳐 한국어 답변 작성, 정책이 임의 데이터임을 고지

날짜가 없으므로 “2일”을 임의의 숙박 일수나 총액으로 환산하지 않고 DB의 1박 가격 기준을 명확히 표시합니다.

## Backend API

```text
GET  /health
GET  /api/mcp/status
GET  /api/mcp/tools
GET  /api/mcp/resources
POST /api/mcp/run
```

Backend에는 Tour와 Weather만 등록되어 있으며 둘 다 `streamable-http`입니다. 이전의 Travel, Policy stdio, Alcohol, Foodmenu 설정은 제거했습니다.

## 현재 검증 결과

- Docker Engine 및 Compose 사용 가능
- pgvector 컨테이너 healthy
- pgvector 확장 `0.8.6`
- 호텔 200건, 관광지 100건 생성
- `192.100.200.232:5432` DB 연결 성공
- Tour MCP 4개 Tool 발견 성공(호텔 정책 RAG 포함)
- Weather MCP 2개 Tool 발견 성공
- Ollama `embeddinggemma` 768차원 임베딩 생성 성공
- 호텔 200건·관광지 100건·호텔 정책 600건, 총 900개 벡터 문서 적재 성공
- 부산 12만 원 이하 호텔 검색 후 해당 호텔만 대상으로 정책 벡터 검색 성공
- Backend에서 두 MCP 서버 연결 성공
- Frontend HTTP 200 성공

아직 API 키가 없어 다음 항목은 미검증입니다.

- OpenAI Agent가 세 Tool을 자율 호출한 최종 답변
- 기상청 현재 날씨 실제 응답

Weather의 `get_next_week_weather`는 현재 코드상 `temporary` 응답이며 실제 중기예보는 아직 구현되지 않았습니다.

## 상세 문서

- [아키텍처](resources/docs/architecture.md)
- [DB 준비](resources/docs/database.md)
- [외부 API 설정](resources/docs/api-setup.md)
- [강사 피드백 및 반영 내용](resources/docs/instructor-feedback.md)
