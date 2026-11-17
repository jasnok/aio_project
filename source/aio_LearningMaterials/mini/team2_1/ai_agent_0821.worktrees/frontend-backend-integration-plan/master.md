# Cafe & Restaurant Recommendation AI Agents — Codex Master Prompt

당신은 현재 저장소의 구조와 구현 패턴을 유지하면서 **카페 주문 추천 AI Agent**와 **맛집 추천 AI Agent**를 추가하는 리드 개발자다. 단순 설계안만 작성하지 말고, 기존 코드를 먼저 분석한 후 실제 구현, 테스트, 실행 문서 정리까지 완료하라.

## 1. 작업 원칙

- 기존 프로젝트의 디렉터리 구조, 코딩 스타일, Agent 실행 흐름, Tool registry, FastAPI router, Streamlit API client 패턴을 우선 재사용한다.
- 기존 여행 Agent 및 기존 API와 테스트가 깨지지 않도록 하위 호환성을 유지한다.
- frontend는 **Python + Streamlit**, backend는 **Python + FastAPI**를 사용한다.
- 외부 DB나 외부 추천 API는 사용하지 않고, 주제별 Python mock 데이터를 사용한다.
- LLM은 사용자의 자연어에서 Tool과 arguments를 선택하고, 실제 검색·필터링·계산은 Python Tool이 수행하게 한다.
- 모든 Tool 입력은 Pydantic으로 검증하고, 허용 목록(allowlist)에 등록된 Tool만 실행한다.
- 카페 Agent가 맛집 Tool을, 맛집 Agent가 카페 Tool을 선택하지 못하도록 Agent별 Tool 목록을 분리한다.
- API 키가 없는 환경에서도 mock Tool 직접 실행, API 테스트, 화면의 기본 조회 기능을 확인할 수 있게 한다. LLM Agent Cycle에 API 키가 필요하다면 화면과 문서에 명확히 표시한다.
- 불필요한 프레임워크나 복잡한 추상화를 추가하지 않는다.
- 의미 있는 함수와 공개 API에는 짧고 명확한 한국어 docstring을 작성한다.

## 2. 역할 분담

작업 경계를 다음 네 역할로 나눈다. 병렬 작업이 가능하다면 역할별로 분리하되, 공통 API 계약은 backend 구현 전에 먼저 합의된 단일 스키마를 사용한다.

### Frontend 1 — 카페 Agent 화면

- 카페 주문 조건 입력 UI
- mock Tool 직접 실행 UI
- 자연어 질문 기반 Agent Cycle UI
- 추천 결과, 선택된 Tool, arguments, 실행 결과, 최종 답변 표시
- 입력 검증 오류와 백엔드 연결 오류 표시

### Frontend 2 — 맛집 추천 Agent 화면

- 맛집 검색 조건 입력 UI
- mock Tool 직접 실행 UI
- 자연어 질문 기반 Agent Cycle UI
- 추천 결과, 선택된 Tool, arguments, 실행 결과, 최종 답변 표시
- 입력 검증 오류와 백엔드 연결 오류 표시

### Backend 1 — 카페 Agent

- 카페 요청/응답 Pydantic schema
- 카페 메뉴 mock 데이터
- 카페 추천 Tool과 Agent instructions
- 카페 전용 API endpoint
- 단위 및 API 테스트

### Backend 2 — 맛집 추천 Agent

- 맛집 요청/응답 Pydantic schema
- 맛집 mock 데이터
- 맛집 추천 Tool과 Agent instructions
- 맛집 전용 API endpoint
- 단위 및 API 테스트

## 3. 확정 데이터 스키마

아래 필드명과 타입을 API, Tool schema, frontend 입력값에서 일관되게 사용한다. Python 내부 필드명은 영문 snake_case로 작성하고, Streamlit 라벨과 설명은 한국어로 표시한다.

### 카페 주문 조건 `CafeRecommendationArgs`

| 한글명 | 필드명 | 타입 | 검증 조건 |
|---|---|---:|---|
| 카테고리 | `category` | `str` | 빈 문자열 금지 |
| 가격 | `price` | `int` | 0 이상, 메뉴 1개 기준 최대 예산으로 해석 |
| 온도 | `temperature` | `str` | 음료 온도 문자열(예: `HOT`, `ICE`), 빈 문자열 금지 |
| 사이즈 | `size` | `str` | 빈 문자열 금지 |
| 수량 | `quantity` | `int` | 1 이상 |

주의: 요구사항에 따라 카페의 `category`, `temperature`, `size`는 **string**이고, `price`와 `quantity`는 **integer**다. 임의로 필드 타입을 바꾸지 않는다.

### 맛집 추천 조건 `RestaurantRecommendationArgs`

| 한글명 | 필드명 | 타입 | 검증 조건 |
|---|---|---:|---|
| 지역 | `region` | `str` | 빈 문자열 금지 |
| 음식 카테고리 | `food_category` | `str` | 빈 문자열 금지 |
| 가격 | `price` | `int` | 0 이상, 1인 기준 최대 예산으로 해석 |
| 알러지 | `allergy` | `str` | 알러지 없음도 문자열(예: `없음`)로 전달 |

스키마에 정의되지 않은 추가 입력은 금지한다. 응답 데이터에는 추천 표시를 위해 `name`, `description`, `matched_conditions`, `source` 등의 필드를 추가할 수 있지만, 그 구조는 Pydantic 응답 모델 또는 명확한 TypedDict/dict 계약으로 관리한다.

## 4. Mock 데이터 요구사항

### 카페 mock 데이터

- 아래 초기 목록처럼 **10개 이내**의 메뉴를 제공한다.
- 커피, 논커피, 티, 디저트 등 여러 카테고리를 포함한다.
- 각 항목은 검색 조건을 실제로 필터링할 수 있는 값을 가져야 한다.
- 정수형 메뉴 가격, 제공 가능한 온도, 사이즈를 포함한다.
- quantity를 반영한 주문 정보 또는 추천 요약을 반환한다.
- 일치 결과가 없으면 빈 목록과 이해하기 쉬운 안내 메시지를 반환한다.

권장 초기 mock 데이터는 다음과 같다. `name`은 추천 결과 표시용 보조 필드이고, `quantity`는 재고가 아니라 예시 주문 수량이다.

| name | category | price | temperature | size | quantity |
|---|---|---|---|---|---:|
| 아메리카노 | 커피 | 3500 | HOT | Tall | 1 |
| 아이스 아메리카노 | 커피 | 4000 | ICE | Grande | 2 |
| 카페라떼 | 커피 | 4800 | HOT | Grande | 1 |
| 바닐라라떼 | 커피 | 5300 | ICE | Grande | 1 |
| 콜드브루 | 커피 | 5000 | ICE | Tall | 2 |
| 초콜릿라떼 | 논커피 | 5200 | HOT | Tall | 1 |
| 딸기스무디 | 논커피 | 6500 | ICE | Grande | 1 |
| 유자차 | 티 | 4500 | HOT | Tall | 1 |
| 복숭아아이스티 | 티 | 3800 | ICE | Grande | 2 |
| 치즈케이크 | 디저트 | 6000 | 해당 없음 | Piece | 1 |

카페 가격은 원 단위 정수로 저장한다. 추천 요청의 `price`는 메뉴 1개 기준 최대 예산으로 사용하며, 해당 금액 이하인 메뉴만 추천한다. 온도 문자열은 음료의 경우 `HOT` 또는 `ICE`, 온도가 없는 디저트는 `해당 없음`을 사용한다. 실제 추천 요청의 `quantity`는 사용자가 입력한 값으로 mock 항목의 예시 수량을 대체하고, `메뉴 가격 × quantity`로 총 주문 금액을 계산하여 주문 요약에 반영한다.

### 맛집 mock 데이터

- 아래 초기 목록처럼 **10개 이내**의 식당을 제공한다.
- 여러 지역과 한식, 중식, 일식, 양식 등 다양한 음식 카테고리를 포함한다.
- 1인 기준 가격과 알러지 관련 재료 정보를 포함한다.
- 지역, 음식 카테고리, 최대 가격을 기준으로 필터링한다.
- 사용자가 입력한 알러지와 충돌하는 식당은 추천에서 제외한다.
- 알러지 필터링은 안전을 보장하는 의료 판단이 아님을 응답과 UI에 짧게 고지한다.
- 일치 결과가 없으면 빈 목록과 이해하기 쉬운 안내 메시지를 반환한다.

권장 초기 mock 데이터는 다음과 같다. `name`은 추천 결과 표시용 보조 필드이며, `allergy`는 해당 식당 메뉴에 포함되거나 교차 접촉할 수 있는 주요 알러지 유발 재료를 나타낸다.

| name | region | food_category | price | allergy |
|---|---|---|---:|---|
| 서울김치마을 | 서울 | 한식 | 12000 | 새우젓 |
| 강남면옥 | 서울 | 한식 | 15000 | 메밀 |
| 홍대파스타 | 서울 | 양식 | 18000 | 우유, 밀, 달걀 |
| 부산바다횟집 | 부산 | 일식 | 25000 | 생선, 조개류 |
| 해운대밀면 | 부산 | 한식 | 10000 | 밀, 달걀 |
| 제주흑돼지집 | 제주 | 한식 | 22000 | 대두 |
| 제주바다국수 | 제주 | 한식 | 11000 | 밀, 조개류 |
| 대구마라공방 | 대구 | 중식 | 14000 | 땅콩, 대두 |
| 인천차이나키친 | 인천 | 중식 | 16000 | 새우, 대두, 밀 |
| 대전그린테이블 | 대전 | 비건 | 13000 | 견과류, 대두 |

맛집 Tool은 사용자 입력 `allergy`가 `없음`일 때 알러지 조건으로 제외하지 않는다. 그 외에는 쉼표로 구분된 알러지 문자열을 정규화하여 mock 데이터의 알러지 항목과 하나라도 겹치는 식당을 제외한다. 부분 문자열만으로 잘못 판정하지 않도록 구분된 항목 단위로 비교한다.

mock 데이터는 backend 도메인 디렉터리 안의 별도 모듈에 두어 Tool 로직과 분리한다.

## 5. 필요한 Agent와 Tool

### 카페 Agent

- Agent 이름 예시: `cafe_recommendation_agent`
- Tool 이름: `recommend_cafe_menu`
- 역할: 자연어 요청에서 카테고리, 최대 가격, 온도, 사이즈, 수량을 추출하고 카페 추천 Tool을 선택한다.
- 필수값이 부족하면 값을 추측하지 말고 사용자에게 필요한 정보를 질문한다.
- 최종 답변은 Tool Result에 포함된 정보만 사용한다.

### 맛집 추천 Agent

- Agent 이름 예시: `restaurant_recommendation_agent`
- Tool 이름: `recommend_restaurants`
- 역할: 자연어 요청에서 지역, 음식 카테고리, 최대 가격, 알러지를 추출하고 맛집 추천 Tool을 선택한다.
- 필수값이 부족하면 값을 추측하지 말고 사용자에게 필요한 정보를 질문한다.
- 알러지 입력이 없으면 반드시 확인 질문을 하며 임의로 `없음`을 넣지 않는다.
- 최종 답변은 Tool Result에 포함된 정보만 사용하고 알러지 주의 문구를 포함한다.

각 Tool은 다음을 만족해야 한다.

- Pydantic 입력 검증
- 추가 필드 거부
- 읽기 전용 mock 데이터 조회
- 결정적인(deterministic) 결과
- 표준 성공/오류 응답
- Tool registry allowlist 등록
- Agent별 Tool definition 조회 가능

## 6. Backend API 계약

기존 router 스타일에 맞추되 아래와 같은 명확한 endpoint를 제공한다. 프로젝트의 기존 prefix 규칙과 충돌하면 동일 의미를 유지하는 범위에서 조정할 수 있다.

- `GET /api/recommendations/cafe/tools`
- `POST /api/recommendations/cafe/run`
- `POST /api/recommendations/cafe/complete`
- `GET /api/recommendations/restaurants/tools`
- `POST /api/recommendations/restaurants/run`
- `POST /api/recommendations/restaurants/complete`

`run`은 LLM 없이 mock Tool을 직접 실행하고, `complete`는 Tool 선택 → Python Tool 실행 → 최종 자연어 답변의 Agent Cycle을 수행한다.

공통 request/response 모델을 재사용하되 OpenAPI에서 두 도메인의 입력 스키마와 설명을 쉽게 확인할 수 있게 한다. 예상 가능한 검증 실패는 500이 아니라 기존 프로젝트의 표준 Tool validation error 또는 적절한 4xx 응답으로 처리한다.

## 7. Streamlit 화면 요구사항

기존 `frontend/app.py` navigation에 다음 두 페이지를 추가한다.

- `카페 추천 Agent`
- `맛집 추천 Agent`

각 페이지에는 다음 두 탭 또는 명확히 구분된 영역을 제공한다.

1. **조건으로 바로 추천**: 입력 widget → Tool 직접 실행 → 추천 결과 표시
2. **AI Agent에게 질문**: 자연어 입력 → Agent Cycle 실행 → Tool 선택, arguments, Tool Result, 최종 답변 표시

카페 화면에서는 `temperature`를 문자열 widget/selectbox로 받고, `price`와 `quantity`를 정수 widget으로 받는다. 맛집 화면에서는 `price`를 정수 widget으로 받고 나머지는 문자열 widget/selectbox로 받는다.

추천 목록은 `st.json`만 사용하지 말고 사용자가 읽기 쉬운 card, dataframe 또는 container 형태로 표시한다. 디버깅용 trace와 원본 JSON은 expander 안에 둔다.

frontend의 HTTP 호출은 기존 공통 API client를 재사용하고, endpoint별 wrapper 함수를 추가한다. 화면 파일에서 직접 `httpx`를 호출하지 않는다.

## 8. 테스트 요구사항

다음 항목을 pytest로 검증한다.

- 카페와 맛집 Tool이 registry/allowlist에 올바르게 등록됨
- Agent별 Tool 목록이 서로 격리됨
- 모든 정상 mock 조건 조회
- 카페 quantity가 0 이하일 때 검증 실패
- 카페 price가 음수일 때 검증 실패
- 잘못된 타입과 알려지지 않은 추가 argument 거부
- 맛집 price가 음수일 때 검증 실패
- 알러지 충돌 식당 제외
- 결과 없음 처리
- 허용되지 않은 Tool 실행 차단
- 새 API endpoint의 정상/오류 응답
- 기존 테스트 전체 회귀 실행

LLM 호출 테스트는 실제 네트워크를 사용하지 말고 기존 방식에 맞춰 mock/monkeypatch한다.

## 9. 문서와 실행 방법

README 또는 적절한 프로젝트 문서에 다음을 추가한다.

- 새 디렉터리와 파일의 역할
- 카페/맛집 Agent 실행 흐름
- backend 실행 명령
- frontend 실행 명령
- 테스트 실행 명령
- mock 데이터 사용 사실
- LLM Agent Cycle에 필요한 환경 변수
- curl 또는 JSON 요청 예시 각 1개 이상

## 10. 완료 조건

다음 조건을 모두 충족해야 작업을 완료한 것으로 본다.

- 두 Agent와 두 Tool이 실제로 동작한다.
- Tool 직접 실행은 API 키 없이 동작한다.
- 두 Streamlit 페이지에서 입력 및 결과 확인이 가능하다.
- 스키마 타입이 요구사항과 정확히 일치한다.
- 기존 기능과 기존 테스트가 깨지지 않는다.
- 새 테스트와 전체 테스트가 통과한다.
- import/문법 오류가 없다.
- 변경된 파일과 핵심 설계 결정을 최종 보고에 요약한다.

## 11. Codex 작업 순서

1. 저장소의 `AGENTS.md`, README, backend Agent/Tool/router/schema, frontend navigation/client/page 구조를 먼저 읽는다.
2. 구현 전 현재 테스트를 실행해 기준 상태를 확인한다.
3. 공통 API 계약과 파일 경계를 정한다.
4. backend의 schema → mock data → Tool → registry/executor → Agent → router 순서로 구현한다.
5. frontend client → 카페 page → 맛집 page → navigation 순서로 구현한다.
6. 단위 테스트와 API 테스트를 추가한다.
7. 전체 테스트와 Python compile/import 검사를 실행한다.
8. 가능한 경우 Streamlit 화면을 실행해 두 페이지의 렌더링 오류를 확인한다.
9. 문서를 갱신한다.
10. 최종 응답에는 구현 결과, 테스트 결과, 남은 제한 사항만 간결하게 보고한다.

중간에 사소한 이름 선택이 필요하면 기존 프로젝트 관례에 맞춰 합리적으로 결정하고 계속 진행하라. 단, 위에 확정된 필드명과 타입, 기술 스택, 두 Agent의 도메인 분리는 변경하지 마라.
