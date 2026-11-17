# 카페 Agent Frontend 작업 계획

## 1. 목표와 작업 범위

이 문서는 `master.md`의 역할 분담 중 **Frontend 1 — 카페 Agent 화면**만 구현하기 위한 계획이다. `backend_plan.md`의 카페 API 계약을 기준으로 Streamlit 화면과 client wrapper를 설계한다. 이번 단계에서는 계획만 수립하며 Python 코드, 테스트, 설정, 문서는 수정하지 않는다.

### 구현 목표

- 기존 `frontend/app.py` navigation에 `카페 추천 Agent` 페이지 추가
- 카페 주문 조건 입력 UI (`CafeRecommendationArgs` 필드만)
- mock Tool 직접 실행 UI (`POST /api/recommendations/cafe/run`)
- 자연어 질문 기반 Agent Cycle UI (`POST /api/recommendations/cafe/complete`)
- 추천 결과, 선택된 Tool, arguments, 실행 결과, 최종 답변 표시
- 입력 검증 오류와 백엔드 연결 오류 표시
- 기존 공통 API client를 재사용하는 카페 전용 wrapper 추가
- API 키 없이 `/run`과 기본 조회를 확인할 수 있게 하고, `/complete`는 LLM 필요를 화면에 명시

### 이번 담당 범위에서 제외

- 맛집 추천 Agent 화면 (`Frontend 2`)
- 카페/맛집 backend schema, mock 데이터, Tool, Agent, router, 테스트
- 화면 파일에서 `httpx` 직접 호출
- 스키마에 없는 추가 입력 필드
- 이번 계획 단계에서의 코드 작성과 화면 실행

---

## 2. 현재 저장소 분석 결과 (재사용할 패턴)

기존 frontend는 아래 경계를 따른다. 카페 화면도 같은 패턴을 유지한다.

| 역할 | 위치 | 카페 작업에서 할 일 |
|---|---|---|
| 공통 HTTP | `frontend/core/api_client.py` | 재사용만. `request()`, `BackendAPIError`를 그대로 사용 |
| endpoint wrapper | `frontend/clients/agent_client.py` | 카페 전용 함수 3개 추가 |
| 화면 | `frontend/app_pages/*.py` | 카페 페이지 1개 추가 |
| navigation | `frontend/app.py` | `st.Page` + sidebar `st.page_link` 추가 |

기존 화면 패턴:

- `15_tool_run.py`: `run_tool(tool_name, arguments)` → `success`면 `data`, 아니면 `error` 표시, `BackendAPIError`는 `st.error`
- `17_agent_cycle.py`: `complete_tool_loop(message, tool_choice)` → decision / tool_result / final_answer / expander(trace)
- 페이지에서 HTTP를 직접 치지 않고 `clients.agent_client`만 import

기존 공통 응답 모델 (`backend/app/schemas/stage_03.py`)을 카페 endpoint도 재사용한다.

- `ToolRunRequest`: `{ "tool_name": str, "arguments": dict }`
- `ToolRunResult`: `{ "success": bool, "tool_name": str, "data": Any | null, "error": dict | null }`
- `ToolCompleteRequest`: `{ "message": str, "tool_choice": "auto" | "none" | "required" }`
- `ToolCompleteResult`: `{ "provider", "question", "decision", "tool_result", "final_answer", "trace" }`
- `ToolSelectionResult.decision`: `tool_name`, `arguments`, `needs_clarification`, `follow_up_question`, `missing_arguments` 등

---

## 3. Frontend가 맞춰야 할 Backend 계약

`backend_plan.md` 기준. backend 구현이 끝나기 전에도 이 계약을 가정하고 UI를 짠다. 필드명·타입은 `master.md`와 동일해야 한다.

### 3.1 Endpoint

| 용도 | Method | Path | API 키 |
|---|---|---|---|
| 카페 Tool 명세 조회 | `GET` | `/api/recommendations/cafe/tools` | 불필요 |
| mock Tool 직접 실행 | `POST` | `/api/recommendations/cafe/run` | 불필요 |
| Agent Cycle | `POST` | `/api/recommendations/cafe/complete` | 필요 (미설정 시 4xx) |

화면의 HTTP 호출은 이 세 경로만 사용한다. 기존 `/api/tools/*`나 맛집 endpoint는 카페 페이지에서 호출하지 않는다.

### 3.2 입력 모델 `CafeRecommendationArgs`

`/run`의 `arguments`와 화면 widget 값은 아래 필드만 보낸다. 추가 키 금지.

| 한글 라벨 | 필드명 | 타입 | widget | 검증 (frontend 선검증) |
|---|---|---|---|---|
| 카테고리 | `category` | `str` | selectbox | 빈 문자열 금지 |
| 가격 | `price` | `int` | number_input (`min_value=0`, `step=1`) | 0 이상, 메뉴 1개 최대 예산 |
| 온도 | `temperature` | `str` | selectbox | 빈 문자열 금지 |
| 사이즈 | `size` | `str` | selectbox | 빈 문자열 금지 |
| 수량 | `quantity` | `int` | number_input (`min_value=1`, `step=1`) | 1 이상 |

주의:

- `price`는 총 주문 예산이 아니라 **메뉴 1개 단가 상한**이다. 라벨에 이 의미를 적는다.
- `quantity`는 재고가 아니다. 요청 수량이며 backend가 `unit_price * quantity`로 총액을 계산한다.
- Streamlit number_input이 float를 돌려줄 수 있으므로 client로 보내기 전에 `int()`로 맞춘다.
- 문자열은 앞뒤 공백을 제거한 뒤 전송한다. backend도 strip 한다.

### 3.3 UI 선택값 (backend mock과 일치)

backend 권장 mock 10개와 필터가 맞도록 selectbox 옵션을 고정한다. 자유 입력으로 오타를 만들지 않는다.

| 필드 | 옵션 |
|---|---|
| `category` | `커피`, `논커피`, `티`, `디저트` |
| `temperature` | `HOT`, `ICE`, `해당 없음` |
| `size` | `Tall`, `Grande`, `Piece` |

필터는 AND다. 디저트는 mock상 `temperature="해당 없음"`, `size="Piece"`이므로 커피 조건으로 디저트가 나오지 않는 것이 정상이다. 화면에 짧은 안내를 둔다.

### 3.4 `/run` 요청 예시

```json
{
  "tool_name": "recommend_cafe_menu",
  "arguments": {
    "category": "커피",
    "price": 5000,
    "temperature": "HOT",
    "size": "Tall",
    "quantity": 2
  }
}
```

카페 화면의 직접 실행은 Tool 이름을 사용자에게 고르게 하지 않고 `recommend_cafe_menu`로 고정한다. allowlist 밖 Tool은 이 페이지에서 보내지 않는다.

### 3.5 `/run` 성공 시 `data` 계약 (표시용)

backend가 별도 응답 모델로 관리한다. frontend는 아래 키를 기준으로 card/dataframe을 그린다. 키가 없으면 빈 값 처리하고 raw JSON은 expander에 남긴다.

최상위 `data` 예상 필드:

- 요청 조건 (입력 echo)
- 추천 목록
- 추천 개수
- 사용자 안내 메시지
- `source: "mock"`

추천 항목 최소 필드:

| 필드 | 의미 |
|---|---|
| `name` | 메뉴 이름 |
| `category` | 카테고리 |
| `unit_price` | 메뉴 1개 가격 (원) |
| `temperature` | `HOT` / `ICE` / `해당 없음` |
| `size` | `Tall` / `Grande` / `Piece` |
| `quantity` | 요청 수량 (사용자 입력값) |
| `total_price` | `unit_price * quantity` |
| `matched_conditions` | 맞은 조건 |
| `description` | 설명 |

결과 없음: HTTP는 성공(`success: true`)이고 목록은 `[]`, 안내 메시지가 온다. 이를 오류로 표시하지 않고 info/empty 상태로 보여준다.

### 3.6 `/complete` 요청 예시

```json
{
  "message": "아이스 아메리카노 그란데 2잔, 예산은 잔당 5000원이야",
  "tool_choice": "auto"
}
```

카페 화면 기본값은 `tool_choice="auto"`다. 기존 여행 화면처럼 selectbox를 둘 수는 있으나, 카페 Agent는 Tool이 하나라 필수는 아니다. 디버깅용으로 expander 안에만 두는 것을 권장한다.

### 3.7 오류 계약과 화면 매핑

| 상황 | backend | frontend 표시 |
|---|---|---|
| 연결 실패, timeout, 비JSON | `BackendAPIError` | `st.error` (기존 문구 재사용) |
| 요청 body schema 오류 | HTTP 422 | `BackendAPIError` → `st.error` |
| Tool 입력 검증 실패 | HTTP 200 + `success: false`, `error.code = "TOOL_VALIDATION_ERROR"` | `st.error` + 오류 내용. 연결 오류와 구분 |
| 카페 allowlist 밖 Tool | `error.code = "TOOL_NOT_ALLOWED"` | `st.error` (직접 실행 UI에서는 발생하지 않아야 함) |
| `/complete` API 키 없음 | 422 또는 명확한 4xx | `st.error` + “LLM Agent Cycle에는 API 키가 필요합니다” 안내 |
| OpenAI 호출 실패 | 502 | `st.error` |
| `needs_clarification` | 200, Tool 미실행 | `st.warning(follow_up_question)`, 최종 답변은 추측 메뉴로 채우지 않음 |
| 추천 0건 | 200, 빈 목록 | `st.info(안내 메시지)` |

`_check()`는 4xx/5xx를 예외로 올린다. 검증 실패가 HTTP 200 + `success: false`이면 예외가 아니라 응답 분기로 처리한다. 이 구분을 화면에서 유지한다.

---

## 4. 화면 설계

### 4.1 페이지 위치

- 파일: `frontend/app_pages/18_cafe_agent.py` (다음 번호 사용)
- navigation 라벨: `카페 추천 Agent`
- sidebar: 기존 01~03 expander를 깨지 않고, `04. 추천 Agent` 또는 동등한 새 구간을 추가해 카페 페이지만 넣는다. 맛집 링크는 Frontend 2가 추가한다.

### 4.2 페이지 구성

두 탭으로 나눈다.

1. **조건으로 바로 추천**
   - 5개 widget → 추천 버튼 → `/run`
   - 추천 목록은 card 또는 dataframe (이름, 온도, 사이즈, 단가, 수량, 총액, 설명)
   - `st.json`만으로 본문을 대체하지 않는다
   - mock 데이터 사용 사실, 단가 기준 예산, 디저트 온도/사이즈 안내
   - expander: 요청 JSON, 원본 `ToolRunResult`
2. **AI Agent에게 질문**
   - 자연어 `st.text_area`
   - 예시 질문 몇 개 (selectbox 또는 caption)
   - `/complete` 실행 전 “API 키가 필요합니다” caption
   - 표시 순서: 선택 Tool → arguments → Tool Result(추천 card) → 최종 답변
   - 필수값 부족이면 follow-up question
   - expander: `decision`, `trace`, 원본 JSON

### 4.3 예시 질문 (Agent 탭)

backend가 값을 추측하지 않으므로, 화면 예시는 필수 5요소가 드러나게 한다.

- `핫 아메리카노 톨 사이즈 1잔, 잔당 4000원 이하로 추천해줘`
- `아이스 논커피 그란데 2잔, 예산은 잔당 7000원이야`
- `디저트 치즈케이크, 해당 없음 온도, Piece, 1개, 6000원 이하`

정보가 빠진 질문도 하나 넣어 clarification UI를 확인할 수 있게 한다.

- `커피 추천해줘` → `needs_clarification` 기대

### 4.4 표시 규칙

- 금액은 원 단위 정수로 보여 주고 총액과 단가를 구분한다.
- `source`가 `mock`이면 실제 매장 주문이 아님을 짧게 고지한다.
- LLM이 만든 최종 답변은 Tool Result와 별도 영역에 둔다. 추천 card는 Tool Result 기준으로 그린다.

---

## 5. Client wrapper 설계

`frontend/core/api_client.py`는 수정하지 않는 것을 기본으로 한다.

`frontend/clients/agent_client.py`에만 추가한다.

```python
def get_cafe_tools():
    return request("GET", "/api/recommendations/cafe/tools")

def run_cafe_tool(arguments: dict[str, Any]):
    payload = {"tool_name": "recommend_cafe_menu", "arguments": arguments}
    return request("POST", "/api/recommendations/cafe/run", json=payload)

def complete_cafe_loop(message: str, tool_choice: str = "auto"):
    payload = {"message": message, "tool_choice": tool_choice}
    return request("POST", "/api/recommendations/cafe/complete", json=payload)
```

화면은 `run_cafe_tool` / `complete_cafe_loop`만 호출한다. `get_cafe_tools`는 페이지 상단 또는 expander에서 “사용 가능한 Tool” 확인용으로 선택 호출한다. 실패해도 입력 UI는 막지 않는다.

기존 `run_tool`, `complete_tool_loop`는 여행 Tool Use 페이지용으로 그대로 둔다.

---

## 6. 구현 순서 (코딩 단계, 지금은 실행하지 않음)

1. **기준 확인**  
   기존 Streamlit이 `clients.agent_client` → `core.api_client`로만 호출하는지 다시 확인. backend 카페 router가 아직 없으면 client 시그니처만 맞추고, 연동 검증은 backend 준비 후로 미룬다.

2. **API client wrapper**  
   `get_cafe_tools`, `run_cafe_tool`, `complete_cafe_loop` 추가. path와 payload 키를 backend 계약과 일치시킨다.

3. **카페 페이지 — 조건 탭**  
   widget → `int`/`strip` → `run_cafe_tool` → 성공/검증실패/연결오류/빈 결과 분기 → card/dataframe + expander.

4. **카페 페이지 — Agent 탭**  
   자연어 → `complete_cafe_loop` → decision / clarification / tool_result card / final_answer / API 키 안내 / expander(trace).

5. **navigation**  
   `frontend/app.py`에 페이지 등록. 기존 17개 링크와 여행 Agent 동작은 유지.

6. **연동 스모크 (backend 준비 후)**  
   - API 키 없이 조건 탭 추천
   - 정상 커피 조건, 디저트 조건, 결과 없음
   - Agent 탭 clarification
   - backend 미기동 시 연결 오류 문구
   - 기존 여행 페이지 회귀(화면이 열리는지)

7. **문서**  
   팀 합의 후 README에 카페 화면 실행 방법, mock 사용, `/complete`의 API 키 필요를 추가한다. 루트 README 신설 여부는 `backend_plan.md`와 같이 팀이 정한다.

---

## 7. 예상 파일 변경 범위

### 신규

- `frontend/app_pages/18_cafe_agent.py`

### 수정

- `frontend/clients/agent_client.py` — 카페 wrapper 3개
- `frontend/app.py` — Page 등록 및 sidebar 링크
- 팀이 합의한 README (실행 안내, mock, API 키) — 화면 구현 이후

### 수정하지 않음

- `frontend/core/api_client.py` (재사용만)
- 기존 `01`~`17` 페이지 로직
- backend 전 파일
- 맛집 frontend 파일

---

## 8. Backend와의 접점 (합의 유지)

`backend_plan.md` 6절과 맞춰 frontend가 가정하는 값이다. backend가 바꾸면 이 계획과 화면 옵션을 같이 고친다.

1. `/run`, `/complete` JSON 예시와 오류 코드 (`TOOL_VALIDATION_ERROR`, `TOOL_NOT_ALLOWED`, 422, 502)
2. selectbox 표기: `커피` / `논커피` / `티` / `디저트`, `HOT` / `ICE` / `해당 없음`, `Tall` / `Grande` / `Piece`
3. `data` 추천 항목 필드명: `name`, `unit_price`, `total_price`, `quantity`, `matched_conditions`, `description`, `source`
4. 결과 없음은 200 + 빈 목록 + 메시지 (예외 아님)
5. `/complete` API 키 없음은 4xx, 화면에 LLM 필요 명시
6. 공통 `ToolRunRequest` / `ToolCompleteResult` 재사용

backend 구현 전에는 UI와 client를 계약대로 작성하고, 실제 HTTP 검증은 카페 router merge 이후에 한다.

---

## 9. 완료 기준

- 사이드바에 `카페 추천 Agent`가 보이고 기존 페이지가 깨지지 않는다.
- 조건 탭에서 5개 확정 필드만 입력하고 `/run`으로 추천을 본다.
- `price`/`quantity`는 int, 나머지 조건은 string selectbox다.
- 추천은 card 또는 dataframe으로 읽고, JSON/trace는 expander에만 있다.
- 빈 결과는 오류가 아니라 안내로 보인다.
- 검증 오류(`success: false`)와 연결 오류(`BackendAPIError`)가 구분된다.
- Agent 탭에서 Tool 이름, arguments, Tool Result, 최종 답변이 보인다.
- clarification이면 추가 질문이 보이고 값을 추측해 채우지 않는다.
- `/run`은 API 키 없이 동작하고, `/complete`는 키 필요를 화면에 적는다.
- 페이지에서 `httpx`를 직접 호출하지 않는다.
- 맛집 화면, backend 구현, 스키마 변경은 이 작업에 포함되지 않는다.

---

## 10. 구현 시 주의사항

- 카페 Agent가 맛집 Tool을 부르지 않게, 이 페이지는 카페 endpoint만 사용한다.
- `st.json`만으로 추천 본문을 대체하지 않는다.
- widget 기본값이 mock과 어긋나면 “결과 없음”이 기본 화면이 된다. 첫 기본값은 실제로 맞는 조합으로 둔다. 예: `category=커피`, `temperature=HOT`, `size=Tall`, `price=5000`, `quantity=1` (아메리카노 3500원에 매칭).
- Streamlit rerun 시 불필요한 재요청을 막기 위해 버튼 클릭 시에만 API를 호출한다.
- 공통 `api_client`의 timeout(70초)과 `BACKEND_API_URL`을 카페 페이지에서 재정의하지 않는다.
- Frontend 2와 sidebar 구간이 겹치지 않게, 카페 페이지만 추가하고 맛집 placeholder는 넣지 않는다.
