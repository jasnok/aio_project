# MCP Server 확장 계획

이 디렉터리는 기능별로 독립 실행 가능한 Python MCP Server를 관리한다.
현재 서버는 `weather/`와 `tour/` 패키지이며, MCP Tool 등록 코드와 외부 API·DB 비즈니스 로직을 분리한다.

## 이번 작업의 범위

- 기능 추가: 날씨 서버에 기상청 단기예보 조회서비스 연동과 기상청·Open-Meteo 비교 기능을 추가한다.
- 구조 개선: 날씨와 투어의 기존 기능은 동작을 유지하면서 모듈을 분리한다.
- 범위 제외: 투어 신규 검색 기능과 날씨 특보·대기질 기능은 이번 작업에서 구현하지 않는다. 문서의 “향후” 항목은 확장 지점 예시다.

## 권장 목표 구조

```text
mcp_server/
├── README.md
├── WEATHER_MCP_PLAN.md
├── TOUR_MCP_PLAN.md
├── common/                         # 여러 서버에서 공유할 때만 사용
│   ├── errors.py
│   ├── logger.py
│   └── http_client.py
├── weather/
│   ├── server.py                   # FastMCP 초기화 및 transport 연결
│   ├── config.py
│   ├── tools/                      # 호출 가능한 기능별 MCP Tool
│   │   ├── __init__.py             # Tool 일괄 등록
│   │   ├── current.py              # 현재 날씨 Tool 등록
│   │   ├── forecast.py             # 예보 Tool 등록
│   │   └── compare.py              # 기상청·Open-Meteo 비교 Tool 등록
│   ├── resources/
│   │   └── __init__.py             # 현재는 등록 지점만 제공
│   ├── prompts/
│   │   └── __init__.py             # 현재는 등록 지점만 제공
│   ├── models/                     # 도메인 모델 및 MCP 입출력 schema
│   │   ├── __init__.py             # 외부 공개 모델 진입점
│   │   ├── requests.py              # Tool 입력 모델
│   │   ├── responses.py             # Tool 출력 모델
│   │   ├── weather.py               # Location 모델
│   │   └── compare.py               # 비교 결과 schema
│   ├── services/
│   │   ├── weather_service.py
│   │   ├── kma_client.py
│   │   ├── kma_provider.py
│   │   ├── open_meteo_client.py
│   │   ├── weather_mapper.py
│   │   └── coordinate_converter.py
├── tour/
│   ├── server.py
│   ├── config.py
│   ├── tools/
│   │   ├── __init__.py             # Tool 일괄 등록
│   │   ├── hotels.py               # 숙박 검색 Tool 등록
│   │   ├── spots.py                # 관광지 검색 Tool 등록
│   │   └── details.py              # 장소 상세 조회 Tool 등록
│   ├── resources/
│   │   └── __init__.py             # 현재는 등록 지점만 제공
│   ├── prompts/
│   │   └── __init__.py             # 현재는 등록 지점만 제공
│   ├── models/
│   │   ├── __init__.py             # 외부 공개 모델 진입점
│   │   ├── requests.py              # Tool 입력 모델
│   │   ├── responses.py             # Tool 출력 모델
│   │   └── tour.py                  # 호텔·관광지 도메인 모델
│   ├── services/
│   │   ├── tour_service.py
│   │   ├── tour_db.py
│   │   └── tour_rag.py
└── tests/
    ├── weather/
    └── tour/
```

단계적으로 분리할 때는 기존 파일을 바로 삭제하지 않고, 새 모듈을 만든 후 기존 서버의 Tool을 새 서비스에 연결하고 테스트가 통과한 뒤 정리한다.

## 서버 공통 원칙

- MCP Tool은 입력 schema 검증, 서비스 호출, 사용자에게 반환할 응답 구성만 담당한다.
- 외부 API, DB, 임베딩 모델 호출은 `services`에 둔다.
- 외부 응답 형식은 `models/`의 원본 schema 또는 mapper에서 내부 응답 형식으로 변환한다.
- API 키와 URL은 환경 변수로 관리하고 서버 시작 시 필수 설정을 검증한다.
- 네트워크 요청에는 timeout과 오류 처리를 적용한다. retry·cache는 현재 미구현이다.
- 각 서버는 독립적으로 실행·테스트할 수 있어야 한다.
- `tools/`, `resources/`, `prompts/`는 기능별 파일로 나눈다. 한 파일에 모든 MCP 기능을 등록하지 않는다.
- 각 기능 파일은 MCP decorator와 입력·출력 schema 등록을 담당하고, 실제 업무 로직은 `services/`에 위임한다.
- 각 디렉터리의 `__init__.py`는 등록 순서와 공개 진입점만 관리한다.
- `models/`는 Pydantic 기반 schema와 도메인 모델을 기능별 파일로 분리한다. API 원본 응답 모델과 MCP 공개 응답 모델을 필요하면 별도로 둔다.
- `server.py`는 서버 초기화, 설정 로드, Tool·Resource·Prompt 등록, transport 실행만 담당한다.

## 모듈 연결 계약

```text
server.py → register_tools() → tools/*.py → services/*.py → API / DB / Vector Store
```

각 서버의 `resources/`와 `prompts/`는 각각 등록 함수를 제공한다. 현재 기능이 없으면 빈 등록 함수로 유지하거나 디렉터리 생성을 보류한다. `server.py`가 외부 API client나 DB 구현을 직접 import하지 않도록 한다.
