"""로그인 사용자를 위한 독립 AI 안내원 화면입니다."""

from __future__ import annotations

import streamlit as st
from housing_common.guide_faq import EXAMPLE_QUESTIONS

from app_pages._guide_view import format_answer
from clients.guide_client import GuideAPIError, get_guide_profile, send_guide_message
from core.auth import is_logged_in
from core.ui import page_header


MESSAGE_KEY = "ai_guide_messages"
OWNER_KEY = "ai_guide_owner_id"
NICKNAME_KEY = "ai_guide_nickname"
ERROR_KEY = "ai_guide_error"

def initialize_guide_state() -> None:
    current_user_id = st.session_state.user_id
    if st.session_state.get(OWNER_KEY) != current_user_id:
        st.session_state[OWNER_KEY] = current_user_id
        st.session_state[MESSAGE_KEY] = []
        st.session_state[NICKNAME_KEY] = "회원"
    else:
        st.session_state.setdefault(MESSAGE_KEY, [])
        st.session_state.setdefault(NICKNAME_KEY, "회원")


def load_nickname() -> None:
    if st.session_state.get(NICKNAME_KEY) != "회원":
        return
    response = get_guide_profile(st.session_state.access_token)
    profile = response.get("data") or {}
    st.session_state[NICKNAME_KEY] = profile.get("nickname") or "회원"


def clear_guide_chat() -> None:
    st.session_state[MESSAGE_KEY] = []


page_header("🤖", "AI 안내원", "사이트 이용 방법과 간단한 청약 용어를 안내해 드려요.")

if not is_logged_in():
    st.warning("AI 안내원을 이용하려면 로그인이 필요합니다.")
    st.stop()

if not st.session_state.access_token:
    st.warning("로그인 토큰을 확인할 수 없습니다. 다시 로그인해 주세요.")
    st.stop()

initialize_guide_state()

try:
    load_nickname()
except GuideAPIError as error:
    st.warning(f"닉네임을 불러오지 못했습니다: {error}")

if error_message := st.session_state.pop(ERROR_KEY, None):
    st.error(error_message)

st.subheader(f"{st.session_state[NICKNAME_KEY]}님, 무엇을 도와드릴까요?")
st.caption(
    "사이트 이용 방법과 간단한 청약 용어·계산을 안내합니다. "
    "공고 추천이나 신청 자격 판단은 제공하지 않습니다."
)

if not st.session_state[MESSAGE_KEY]:
    with st.expander("예시 질문 보기"):
        st.markdown("\n\n".join(f"- {question}" for question in EXAMPLE_QUESTIONS))

for message in st.session_state[MESSAGE_KEY]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("사이트 이용 방법이나 간단한 청약 용어를 질문해 주세요")
if prompt:
    history = list(st.session_state[MESSAGE_KEY])
    st.session_state[MESSAGE_KEY].append({"role": "user", "content": prompt})

    try:
        with st.spinner("질문을 분석하고 있습니다..."):
            response = send_guide_message(
                question=prompt,
                messages=history,
                access_token=st.session_state.access_token,
            )
        data = response.get("data") or {}
        st.session_state[MESSAGE_KEY].append(
            {"role": "assistant", "content": format_answer(data)}
        )
    except GuideAPIError as error:
        st.session_state[ERROR_KEY] = str(error)
    st.rerun()

if st.button(
    "새 대화 시작",
    use_container_width=True,
    disabled=not st.session_state[MESSAGE_KEY],
):
    clear_guide_chat()
    st.rerun()
