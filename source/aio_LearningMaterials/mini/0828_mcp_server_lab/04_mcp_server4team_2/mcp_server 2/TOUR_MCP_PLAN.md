# 투어 MCP Server 계획서

## 1. 목표

관광지와 숙박 정보를 지역·카테고리·가격·자연어 검색어로 조회하고, 향후 여행 일정 구성에 필요한 장소 정보를 일관된 형식으로 제공한다.

기존 투어 검색·임베딩 로직을 MCP Tool에서 분리하고 `tour/` 패키지 내부에서 관리한다.

### 이번 구현 범위

1. 기존 `search_hotels`, `search_spots`의 동작과 응답을 유지한다.
2. Tool·Resource·Prompt·Model·Service 디렉터리로 파일을 분리한다.
3. DB·벡터 검색·임베딩 연결을 서비스 계층 뒤로 숨긴다.
4. 장소 상세·주변 검색·일정 생성과 실제 Resource·Prompt는 이번 구현에서 만들지 않는다.

### 현재 구현 상태

| 기능 | 상태 | 현재 동작 |
|---|---|---|
| 호텔 검색 | 구현 | `PostgresTourRepository`를 통해 PostgreSQL/pgvector 검색 |
| 관광지 검색 | 구현 | 도시·카테고리·키워드 조건 검색 |
| 키워드 RAG | 구현 | 키워드가 있을 때 Ollama `api/embed` 호출 |
| Resource·Prompt | 등록 지점만 구현 | 실제 Resource·Prompt 없음 |
| 상세·주변·일정 기능 | 미구현 | 향후 확장 대상 |

## 2. 제공할 MCP Tool

### `search_hotels`

- 입력: 도시, 최대 가격, 검색어, 선택적 숙박 조건
- 출력: 숙소 ID, 이름·설명, 가격, 위치, 편의시설, 검색 점수 또는 거리

### `search_spots`

- 입력: 도시, 카테고리, 검색어
- 출력: 관광지 ID, 이름·설명, 카테고리, 위치, 운영 정보, 검색 점수

### 향후 추가 Tool(이번 범위 제외)

- `get_tour_detail`: 장소 상세 정보
- `search_nearby_places`: 좌표 기준 주변 장소 검색
- `build_itinerary_candidates`: 일정 후보지 조합
- `get_opening_hours`: 운영 시간과 휴무일 조회

## 3. 권장 내부 구조

```text
tour/
├── __init__.py
├── server.py                         # FastMCP 생성, 전체 기능 등록, transport 실행
├── config.py                         # DB·임베딩·서버 환경 변수 로드·검증
├── models/
│   ├── __init__.py                   # 외부 공개 모델과 schema 진입점
│   ├── requests.py                   # 검색·상세 조회 Tool 입력 schema
│   ├── responses.py                  # MCP Tool 출력 schema
│   ├── tour.py                       # 호텔·관광지 도메인 모델
│   └── search.py                     # 필터·정렬·페이지·검색 결과 모델
├── tools/
│   ├── __init__.py                   # 투어 Tool 전체를 서버에 등록
│   ├── hotels.py                     # search_hotels 입력 검증·응답 구성
│   ├── spots.py                      # search_spots 입력 검증·응답 구성
│   ├── details.py                    # 미구현 확장 파일
│   └── nearby.py                     # 미구현 확장 파일
├── resources/
│   ├── __init__.py                   # 투어 Resource 전체를 서버에 등록
│   ├── categories.py                 # 미구현 Resource 확장 파일
│   ├── cities.py                     # 미구현 Resource 확장 파일
│   └── schemas.py                    # 미구현 Resource 확장 파일
├── prompts/
│   ├── __init__.py                   # 투어 Prompt 전체를 서버에 등록
│   ├── itinerary.py                  # 미구현 Prompt 확장 파일
│   └── recommendation.py             # 미구현 Prompt 확장 파일
└── services/
    ├── __init__.py                   # 서비스 공개 진입점
    ├── tour_service.py               # 검색 조건 조합·limit·정렬·결과 정책
    ├── tour_repository.py            # DB·벡터 DB 접근 인터페이스
    ├── tour_db.py                    # 실제 DB 쿼리와 연결 관리
    ├── tour_rag.py                   # 임베딩 생성과 검색용 벡터 처리
    ├── result_formatter.py           # 내부 모델을 MCP 응답으로 변환
    └── filters.py                    # 가격·카테고리·지역 필터 처리
```

검색 흐름은 다음과 같이 유지한다.

```text
MCP Tool → TourService → Repository + EmbeddingService → DB/Vector Store
```

### 실제 등록·호출 연결

- `tour/server.py`: `TourService`를 생성하고 Tool·Resource·Prompt 등록 함수를 호출한다.
- `tools/hotels.py`, `tools/spots.py`: 기존 Tool을 등록하고 입력 schema 검증 후 Service만 호출한다.
- `services/tour_service.py`: `search_hotels()`, `search_spots()`와 필터·limit·정렬 정책을 제공한다.
- `services/tour_repository.py`: DB·벡터 저장소 접근 Protocol을 정의한다.
- `services/tour_db.py`: PostgreSQL·pgvector 쿼리와 연결을 담당한다.
- `services/tour_rag.py`: Ollama 임베딩 호출을 담당한다.
- `services/result_formatter.py`: 내부 검색 결과를 공개 response schema로 변환한다.

의존 방향은 Tool → TourService → Repository/EmbeddingService → DB/Vector Store로 고정한다.

### 파일 역할 규칙

- `tools/*.py`: MCP Tool의 이름·설명·입력 schema를 선언하고 `TourService`를 호출한다.
- `resources/*.py`: 카테고리, 지원 도시, 검색 규격처럼 읽기 전용이고 비교적 정적인 정보를 제공한다.
- `prompts/*.py`: 장소 추천·일정 작성에 사용할 프롬프트 템플릿을 정의한다. 검색이나 DB 접근은 하지 않는다.
- `models/requests.py`: Tool 입력값, 필수 여부, 범위, enum, 페이지 조건을 검증한다.
- `models/responses.py`: DB 내부 구조와 분리된 MCP 공개 응답 계약을 정의한다.
- `models/tour.py`: 호텔·관광지·위치·가격 등 투어 도메인 모델을 정의한다.
- `models/search.py`: 검색 필터, 정렬, pagination, 유사도 결과 모델을 정의한다.
- `services/tour_service.py`: Tool 간에 공유되는 검색 정책과 업무 규칙을 담당한다.
- `services/tour_repository.py`: 저장소 구현과 Tool을 분리하는 인터페이스 역할을 한다.
- `services/result_formatter.py`: DB 필드를 외부 공개용 응답 모델로 제한하고 형식을 통일한다.
- `server.py`: 등록 함수 호출과 transport 실행만 담당한다.

## 4. 검색 및 데이터 설계

- 구조화 필터는 벡터 검색보다 먼저 적용해 검색 범위를 줄인다.
- `keyword`가 없으면 일반 필터 검색을 사용하고, 있으면 임베딩 기반 검색을 추가한다.
- 응답에는 내부 DB의 불필요한 필드나 민감 정보를 노출하지 않는다.
- 거리·유사도·가격 정렬 기준을 명시적으로 관리한다.
- 결과가 없을 때 오류 대신 빈 `items`와 `count: 0`을 반환한다.
- 장소 데이터의 출처와 마지막 갱신 시각을 보존한다.

## 5. 환경 변수

```env
TOUR_MCP_HOST=127.0.0.1
TOUR_MCP_PORT=8020
DATABASE_URL=
VECTOR_TABLE_NAME=tour_vectors
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBEDDING_MODEL=embeddinggemma
TOUR_SEARCH_LIMIT=20
```

## 6. 테스트 계획

- 도시·카테고리·가격 입력 검증
- 가격 경계값과 잘못된 값 테스트
- keyword가 없는 일반 검색 테스트
- keyword가 있는 임베딩 검색 테스트
- DB 장애 및 임베딩 서버 timeout 테스트
- 결과 없음, 중복 결과, 정렬 기준 테스트
- 실제 DB 대신 repository mock을 사용한 MCP Tool 테스트
- 도시별 대표 데이터로 end-to-end 검색 테스트

## 7. 기존 코드에서의 이전 순서

1. 기존 DB 검색 로직을 `services/tour_db.py`로 이동하고 `tour_repository.py` Protocol 뒤에 연결한다.
2. `models/`에 request·response·도메인 schema를 정의한다.
3. 기존 임베딩 로직을 `services/tour_rag.py`의 `EmbeddingService`로 이동한다.
4. `TourService`에서 검색 조건, limit, 정렬, 결과 변환을 담당하게 한다.
5. `search_hotels`, `search_spots`가 서비스만 호출하도록 각 `tools/*.py`로 이동한다.
6. 루트 호환 진입점을 만들지 않고 `python -m mcp_server.tour`만 공식 실행 경로로 사용한다.

## 8. 구현 가능성 점검 및 완료 기준

투어 계획은 신규 기능이 아니라 기존 기능을 보존하는 리팩터링 계획으로 구현 가능하다.

- 기존 두 Tool의 입력·출력 계약과 검색 결과가 리팩터링 전과 동일하다.
- `tools/*.py`에서 DB·벡터 DB·임베딩 구현을 직접 호출하지 않는다.
- Repository와 EmbeddingService를 mock으로 교체해 Tool 테스트가 가능하다.
- DB 장애, 임베딩 timeout, 결과 없음이 일관된 공개 응답으로 변환된다.
- `server.py`의 등록 함수만으로 기존 Tool을 모두 등록할 수 있다.
- 향후 Tool 추가 시 기존 Tool 파일을 대규모로 수정하지 않는다.
