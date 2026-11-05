"""카페 추천 Agent 화면입니다. 카페 API만 호출하고 맛집·여행 endpoint는 사용하지 않습니다."""

from typing import Any

import streamlit as st

from clients.agent_client import complete_cafe_loop, get_cafe_tools, run_cafe_tool
from core.api_client import BackendAPIError


CATEGORIES = ["커피", "논커피", "티", "디저트"]
TEMPERATURES = ["HOT", "ICE", "해당 없음"]
SIZES = ["Tall", "Grande", "Piece"]
EXAMPLE_QUESTIONS = [
    "핫 아메리카노 톨 사이즈 1잔, 잔당 4000원 이하로 추천해줘",
    "아이스 논커피 그란데 2잔, 예산은 잔당 7000원이야",
    "디저트 치즈케이크, 해당 없음 온도, Piece, 1개, 6000원 이하",
    "4천원 이하 아이스 그란데 커피 2개 추천해줘",
    "커피 추천해줘",
]


def _format_won(value: Any) -> str:
    try:
        return f"{int(value):,}원"
    except (TypeError, ValueError):
        return str(value)


def _extract_recommendations(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    items = data.get("recommendations")
    if items is None:
        items = data.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _render_recommendation_cards(data: Any) -> None:
    if not isinstance(data, dict):
        st.info("추천 본문을 표시할 수 없어 원본 응답을 expander에서 확인하세요.")
        return

    source = data.get("source", "mock")
    count = data.get("count")
    message = data.get("message") or data.get("guidance") or ""
    recommendations = _extract_recommendations(data)

    if source:
        st.caption(f"데이터 출처: `{source}` · 실제 매장 주문이 아닌 mock 추천입니다.")
    if count is None:
        count = len(recommendations)
    st.write(f"추천 개수: **{count}**")
    if message:
        if recommendations:
            st.success(message)
        else:
            st.info(message)

    if not recommendations:
        if not message:
            st.info("조건에 맞는 메뉴가 없습니다. 카테고리·온도·사이즈·단가 상한을 바꿔 보세요.")
        return

    rows = []
    for item in recommendations:
        with st.container(border=True):
            name = item.get("name", "이름 없음")
            st.subheader(name)
            col1, col2, col3 = st.columns(3)
            col1.write(f"카테고리: {item.get('category', '-')}")
            col2.write(f"온도: {item.get('temperature', '-')}")
            col3.write(f"사이즈: {item.get('size', '-')}")
            col4, col5, col6 = st.columns(3)
            col4.write(f"단가: {_format_won(item.get('unit_price'))}")
            col5.write(f"수량: {item.get('quantity', '-')}")
            col6.write(f"총액: {_format_won(item.get('total_price'))}")
            description = item.get("description")
            if description:
                st.write(description)
            matched = item.get("matched_conditions")
            if matched:
                st.caption(f"일치 조건: {matched}")
        rows.append(
            {
                "메뉴": name,
                "카테고리": item.get("category"),
                "온도": item.get("temperature"),
                "사이즈": item.get("size"),
                "단가": item.get("unit_price"),
                "수량": item.get("quantity"),
                "총액": item.get("total_price"),
            }
        )
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


def _render_tool_error(error: Any) -> None:
    st.error("Tool 실행이 차단되었거나 입력 검증에 실패했습니다. 백엔드 연결 오류가 아닙니다.")
    if isinstance(error, dict):
        code = error.get("code", "")
        message = error.get("message") or error.get("detail") or ""
        if code:
            st.caption(f"오류 코드: `{code}`")
        if message:
            st.write(message)
        st.json(error)
    else:
        st.write(error)


def _render_run_result(result: Any, request_payload: dict[str, Any]) -> None:
    if not isinstance(result, dict):
        st.error("예상과 다른 응답 형식입니다.")
        st.write(result)
        return

    if result.get("success"):
        st.success("카페 추천 Tool 실행 성공")
        _render_recommendation_cards(result.get("data"))
    else:
        _render_tool_error(result.get("error"))

    with st.expander("요청 JSON · 원본 ToolRunResult"):
        st.caption("요청")
        st.json(request_payload)
        st.caption("응답")
        st.json(result)


def _render_complete_result(result: Any) -> None:
    if not isinstance(result, dict):
        st.error("예상과 다른 응답 형식입니다.")
        st.write(result)
        return

    decision = result.get("decision") or {}
    tool_result = result.get("tool_result")
    final_answer = result.get("final_answer") or ""

    st.subheader("1. 선택된 Tool과 arguments")
    st.write(f"Tool: `{decision.get('tool_name') or '없음'}`")
    st.json(decision.get("arguments") or {})
    missing = decision.get("missing_arguments") or []
    if missing:
        st.caption(f"부족한 값: {', '.join(missing)}")

    st.subheader("2. Tool 실행 결과")
    if decision.get("needs_clarification"):
        st.warning(decision.get("follow_up_question") or "필수 정보가 부족합니다. 값을 추측하지 않고 추가 질문이 필요합니다.")
    elif tool_result is None:
        st.info("실행할 Tool이 없습니다.")
    elif isinstance(tool_result, dict) and not tool_result.get("success", True):
        _render_tool_error(tool_result.get("error"))
    elif isinstance(tool_result, dict):
        _render_recommendation_cards(tool_result.get("data"))
    else:
        st.write(tool_result)

    st.subheader("3. 최종 답변")
    if decision.get("needs_clarification"):
        st.info("필수값이 채워지기 전에는 추천 메뉴를 임의로 채우지 않습니다.")
        if final_answer:
            st.write(final_answer)
    elif final_answer:
        st.success(final_answer)
    else:
        st.info("최종 답변이 비어 있습니다.")

    with st.expander("decision · trace · 원본 JSON"):
        st.caption("decision")
        st.json(decision)
        st.caption("trace")
        st.json(result.get("trace") or [])
        st.caption("원본 응답")
        st.json(result)


st.title("☕ 카페 추천 Agent")
st.caption("조건으로 mock Tool을 직접 실행하거나, 자연어로 카페 Agent Cycle을 호출합니다.")
st.info(
    "추천은 외부 DB가 아닌 mock 메뉴 10개를 사용합니다. "
    "가격은 **메뉴 1개 단가 상한**이고, 수량은 재고가 아니라 주문 수량입니다. "
    "카테고리·온도·사이즈·단가를 모두 만족하는 메뉴만 나옵니다. "
    "디저트는 온도 `해당 없음`, 사이즈 `Piece`입니다."
)

with st.expander("사용 가능한 카페 Tool"):
    if st.button("카페 Tool 명세 불러오기"):
        try:
            st.json(get_cafe_tools())
        except BackendAPIError as error:
            st.error(str(error))
            st.caption("Tool 명세 조회에 실패해도 아래 입력 UI는 그대로 사용할 수 있습니다.")

run_tab, agent_tab = st.tabs(["조건으로 바로 추천", "AI Agent에게 질문"])

with run_tab:
    st.subheader("주문 조건")
    st.caption("이 탭은 API 키 없이 `POST /api/recommendations/cafe/run`을 호출합니다.")
    col_a, col_b = st.columns(2)
    with col_a:
        category = st.selectbox("카테고리", CATEGORIES, index=0)
        temperature = st.selectbox("온도", TEMPERATURES, index=0)
        size = st.selectbox("사이즈", SIZES, index=0)
    with col_b:
        price = st.number_input("가격 (메뉴 1개 최대 예산, 원)", min_value=0, value=5000, step=100)
        quantity = st.number_input("수량", min_value=1, value=1, step=1)

    arguments = {
        "category": str(category).strip(),
        "price": int(price),
        "temperature": str(temperature).strip(),
        "size": str(size).strip(),
        "quantity": int(quantity),
    }
    request_payload = {"tool_name": "recommend_cafe_menu", "arguments": arguments}

    if st.button("mock Tool로 바로 추천", type="primary"):
        try:
            result = run_cafe_tool(arguments)
            _render_run_result(result, request_payload)
        except BackendAPIError as error:
            st.error(str(error))
            with st.expander("요청 JSON"):
                st.json(request_payload)

with agent_tab:
    st.subheader("자연어로 카페 Agent에게 질문")
    st.warning("이 탭은 `POST /api/recommendations/cafe/complete`를 사용하며 **OpenAI API 키가 필요**합니다. 키가 없으면 4xx 오류가 납니다.")
    example = st.selectbox("예시 질문", EXAMPLE_QUESTIONS)
    message = st.text_area("질문", value=example, height=120)
    with st.expander("디버깅: tool_choice"):
        tool_choice = st.selectbox("Tool Choice", ["auto", "none", "required"], index=0)
        st.caption("카페 Agent Tool은 `recommend_cafe_menu` 하나뿐입니다. 기본값은 auto입니다.")

    if st.button("Agent Cycle 실행", type="primary"):
        cleaned = message.strip()
        if not cleaned:
            st.error("질문을 입력해 주세요.")
        else:
            try:
                result = complete_cafe_loop(cleaned, tool_choice)
                _render_complete_result(result)
            except BackendAPIError as error:
                st.error(str(error))
                st.caption("LLM Agent Cycle에는 API 키가 필요합니다. 연결 실패라면 backend 실행 상태를 확인해 주세요.")
