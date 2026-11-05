# 강사 피드백 및 반영 내용

팀원들이 변경 이유와 위치를 빠르게 확인할 수 있도록 강사 피드백과 실제 반영 결과를 정리했습니다.

## 1. 불필요한 파일 제거

### 피드백

- `weather_mcp/weather.py`는 필요 없음
- `tour_mcp/tour_database.py`, `tour_embeddings.py`, `tour_server.py`는 필요 없음

### 반영

네 파일은 이전 import 또는 실행 명령을 지원하기 위한 호환 파일이어서 모두 삭제했습니다. 현재 실행 진입점은 다음 두 파일로 통일했습니다.

```text
app/tour/main.py
app/weather/main.py
```

## 2. 루트 tests 폴더가 헷갈림

### 피드백

Tour와 Weather 테스트가 루트 `tests/`에 함께 있어 구분하기 어려움

### 반영

테스트를 삭제하지 않고 각 서버 내부로 이동했습니다.

```text
app/tour/tests/
app/weather/tests/
```

두 서버를 대상으로 하는 HTTP 점검은 `run/check_mcp_http.py`로 분리했습니다.

## 3. 폴더 목적을 직관적으로 표현

### 피드백

- `providers`는 외부 연동 목적이 드러나는 이름으로 변경
- `infrastructure`도 역할이 드러나는 이름으로 변경
- `core/exceptions.py`는 별도 분리 가능

### 반영

```text
기존 tour/providers/                  → app/tour/rag/
기존 tour/infrastructure/database.py → app/tour/database/connection.py
기존 weather/providers/              → app/weather/external_clients/
기존 설정 파일                       → 각 서버의 core/config.py
기존 예외 파일                       → 각 서버의 core/errors.py
```

설정과 예외를 각 서버의 `core/`에 함께 모았습니다. 예외가 한두 개뿐이므로 별도의 `exceptions/` 폴더까지 만들지는 않았습니다.

## 4. RAG 관련 코드 정리

### 피드백

RAG를 사용한다면 별도의 `rag/` 폴더로 관리할 수 있음

### 반영

OpenAI 임베딩 파일에 섞여 있던 책임을 다음처럼 분리했습니다.

```text
app/tour/rag/
├─ embedding_client.py   # OpenAI Embeddings API 호출
├─ document_builder.py   # 호텔·관광지 검색 문서 생성
└─ vector_utils.py       # 콘텐츠 해시와 pgvector 변환
```

다만 다음 책임은 RAG와 다르므로 유지했습니다.

- `services/`: 벡터 검색 여부, fallback, 추천 정책
- `repositories/`: PostgreSQL 및 pgvector SQL
- `database/`: DB 연결과 향후 DB 관련 모듈 확장

## 5. KMA API URL과 버전 설정

### 피드백

KMA API URL을 `.env`로 옮기고 버전 변경 상황을 고려해야 함

### 반영

`app/weather/.env.example`에 다음 설정을 추가했습니다.

```dotenv
KMA_API_BASE_URL=https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
KMA_API_VERSION=2.0
```

`app/weather/core/config.py`에서 URL 형식을 검증합니다. 버전 변경 시 자동 전환하지 않고 URL과 버전을 함께 변경한 뒤 테스트하도록 README에 절차를 기록했습니다.

## 6. SQL·설명서·실행 파일 재분류

### 피드백

- SQL과 설명서를 목적에 맞게 모아서 관리
- 루트를 `app`, SQL/자료, README, 원클릭 실행 중심으로 단순화

### 반영

```text
resources/
├─ database/
│  ├─ sql/
│  └─ populate_tour_documents.py
├─ data/
└─ docs/
```

SQL과 DB 적재 스크립트를 `resources/database/`에 모으고, SQL에는 적용 순서를 알 수 있도록 `001`, `002`, `003` 접두사를 붙였습니다.

## 7. README와 제출 문서 통합

### 피드백

`SUBMISSION.md`를 `README.md`에 포함할 수 있음

### 반영

`SUBMISSION.md`를 삭제하고 설치, 실행, 테스트, DB 준비, 환경변수, 제출 전 확인 내용을 루트 `README.md`에 통합했습니다.

## 8. 원클릭 실행 및 테스트

### 피드백

클릭 또는 명령 한 번으로 전체 MCP 서버를 검사할 수 있는 파일이 있으면 좋음

### 반영

실행 관련 파일을 `run/`에 모았습니다.

```text
run/
├─ run_servers.ps1
├─ run_tests.ps1
└─ check_mcp_http.py
```

사용법:

```powershell
.\run\run_servers.ps1
.\run\run_tests.ps1
.\run\run_tests.ps1 -Integration
```

## 최종 루트 구조

```text
app/
resources/
run/
README.md
requirements.txt
.gitignore
```

루트에서는 실제 코드, 프로젝트 자료, 실행 도구의 세 영역만 보이며 세부 책임은 각 영역 내부에서 구분됩니다.
