import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv


FRONTEND_ROOT = Path(__file__).resolve().parent
load_dotenv(FRONTEND_ROOT / ".env")
BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")


def get(path: str) -> dict:
    response = httpx.get(f"{BASE_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def post(path: str, payload: dict) -> dict:
    response = httpx.post(f"{BASE_URL}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def error_detail(error: httpx.HTTPError) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        try:
            return str(error.response.json().get("detail", error))
        except ValueError:
            return error.response.text or str(error)
    return str(error)


st.set_page_config(page_title="Tour & Weather MCP", page_icon="🧭", layout="wide")
st.title("Tour & Weather MCP")
st.caption(f"Backend `{BASE_URL}`가 두 Streamable HTTP MCP 서버를 호출합니다.")

try:
    status = get("/api/mcp/status")
    if status["status"] == "connected":
        st.success(f"모든 MCP 연결 성공 · Tool {status['tool_count']}개")
    else:
        st.warning(f"일부 MCP 연결 실패 · 사용 가능 Tool {status['tool_count']}개")

    for server in status["servers"]:
        icon = "✅" if server["status"] == "connected" else "❌"
        st.write(
            f"{icon} `{server['name']}` · {server['transport']} · "
            f"{server['endpoint']} · Tool {server['tool_count']}개"
        )
        if server.get("error"):
            st.caption(server["error"])
except httpx.HTTPError as error:
    st.error(f"Backend에 연결할 수 없습니다: {error_detail(error)}")

if st.button("MCP Tool 목록 새로고침"):
    try:
        st.json(get("/api/mcp/tools"))
    except httpx.HTTPError as error:
        st.error(f"Backend 호출 실패: {error_detail(error)}")

question = st.text_input(
    "질문",
    "부산으로 2일 여행을 가려고 해. 120000원 이하 호텔을 검색해줘. "
    "오늘 날씨 알려줘. 당일 취소에 대해 알려줘.",
)
if st.button("MCP Agent 실행", type="primary"):
    try:
        result = post("/api/mcp/run", {"question": question})
        st.success(result["answer"])
        left, right = st.columns(2)
        left.metric("GPT 호출 횟수", result["llm_calls"])
        right.metric("실행된 Tool 수", len(result["trace"]))
        st.subheader("Agent가 선택한 MCP Tool")
        for item in result["trace"]:
            title = f"Round {item['round']} · {item['server']} · {item['tool']}"
            with st.expander(title, expanded=True):
                st.caption(f"Public Tool: {item['public_tool']}")
                st.write("Arguments")
                st.json(item["arguments"])
                st.write("Tool Result")
                st.code(item["result"])
                if item["is_error"]:
                    st.error("MCP Tool 실행 오류")
        with st.expander("전체 응답 JSON"):
            st.json(result)
    except httpx.HTTPError as error:
        st.error(f"Backend 호출 실패: {error_detail(error)}")
