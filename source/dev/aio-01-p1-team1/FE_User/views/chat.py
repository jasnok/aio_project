"""로그인 사용자를 위한 AI 채팅 상담 화면입니다."""

import streamlit as st
from uuid import uuid4

from clients.chat_client import (
    ChatAPIError,
    delete_chat_history,
    get_chat_history,
    get_chat_profile,
    save_chat_summary,
    send_chat_message,
)
from core.auth import is_logged_in
from core.ui import page_header
from core.session_result import session_result


from core.chat_state import (
    MESSAGE_KEY,
    NICKNAME_KEY,
    END_CONFIRM_KEY,
    FLASH_KEY,
    ERROR_KEY,
    SAVE_REQUEST_KEY,
    HISTORY_ATTEMPTED_KEY,
    HISTORY_READY_KEY,
    clear_current_chat,
    initialize_chat_state,
)
from views.chat_summaries import show_saved_summaries


def load_nickname() -> None:
    response = session_result(
        st.session_state, "ai-chat-profile-cache",
        (st.session_state.user_id, st.session_state.access_token),
        lambda: get_chat_profile(st.session_state.access_token),
    )
    profile = response.get("data") or {}
    st.session_state[NICKNAME_KEY] = profile.get("nickname") or "회원"


def render() -> None:
    page_header("💬", "AI 채팅 상담", "청약 자격이나 신청 방법을 편하게 물어보세요.")

    if not is_logged_in():
        st.warning("AI 채팅 상담을 이용하려면 로그인이 필요합니다.")
        st.stop()

    if not st.session_state.access_token:
        st.warning("로그인 토큰을 확인할 수 없습니다. 다시 로그인해 주세요.")
        st.stop()

    initialize_chat_state()

    if not st.session_state[HISTORY_ATTEMPTED_KEY]:
        st.session_state[HISTORY_ATTEMPTED_KEY] = True
        try:
            response = get_chat_history(st.session_state.access_token)
            st.session_state[MESSAGE_KEY] = response.get("data") or []
            st.session_state[HISTORY_READY_KEY] = True
        except ChatAPIError as error:
            st.session_state[ERROR_KEY] = str(error)

    try:
        load_nickname()
    except ChatAPIError as error:
        st.warning(f"닉네임을 불러오지 못했습니다: {error}")

    if flash_message := st.session_state.pop(FLASH_KEY, None):
        st.success(flash_message)
    if error_message := st.session_state.pop(ERROR_KEY, None):
        st.error(error_message)

    st.subheader(f"{st.session_state[NICKNAME_KEY]}님, 무엇을 도와드릴까요?")
    st.caption("현재 대화는 Redis에 1시간 동안 임시 보관됩니다. 대화 저장 시 요약본으로 저장됩니다.")
    st.warning("AI 답변은 검증된 데이터가 아닐 수 있습니다. 중요한 내용은 공식 공고와 담당 기관에서 확인해 주세요.")

    if st.button("진행 대화 새로고침"):
        try:
            response = get_chat_history(st.session_state.access_token)
            st.session_state[MESSAGE_KEY] = response.get("data") or []
            st.session_state[HISTORY_READY_KEY] = True
            st.session_state.pop(SAVE_REQUEST_KEY, None)
            st.rerun()
        except ChatAPIError as error:
            st.session_state[HISTORY_READY_KEY] = False
            st.error(str(error))

    show_saved_summaries()
    if not st.session_state[HISTORY_READY_KEY]:
        st.warning("진행 대화를 확인하지 못했습니다. '진행 대화 새로고침'이 성공하면 상담을 계속할 수 있습니다.")
    st.divider()

    for chat_message in st.session_state[MESSAGE_KEY]:
        with st.chat_message(chat_message["role"]):
            st.write(chat_message["content"])

    prompt = st.chat_input("상담 질문을 입력하세요", disabled=not st.session_state[HISTORY_READY_KEY])
    if prompt:
        try:
            with st.spinner("AI 상담 답변을 생성하고 있습니다..."):
                response = send_chat_message(
                    question=prompt,
                    access_token=st.session_state.access_token,
                )
            data = response.get("data") or {}
            st.session_state[MESSAGE_KEY].extend(
                [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": data.get("answer") or "답변이 비어 있습니다."},
                ]
            )
            st.session_state.pop(SAVE_REQUEST_KEY, None)
        except ChatAPIError as error:
            st.session_state[ERROR_KEY] = str(error)
        st.rerun()

    end_col, save_col = st.columns(2)

    with end_col:
        if st.button("대화 종료", use_container_width=True, disabled=not st.session_state[HISTORY_READY_KEY]):
            st.session_state[END_CONFIRM_KEY] = True

    with save_col:
        save_clicked = st.button(
            "대화 저장",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state[HISTORY_READY_KEY] or len(st.session_state[MESSAGE_KEY]) < 2,
        )

    if st.session_state[END_CONFIRM_KEY]:
        st.warning("현재 상담 내용을 모두 삭제하시겠습니까? 저장하지 않은 대화는 복구할 수 없습니다.")
        cancel_col, confirm_col = st.columns(2)
        with cancel_col:
            if st.button("취소", use_container_width=True):
                st.session_state[END_CONFIRM_KEY] = False
                st.rerun()
        with confirm_col:
            if st.button("종료하기", type="primary", use_container_width=True, disabled=not st.session_state[HISTORY_READY_KEY]):
                try:
                    delete_chat_history(st.session_state.access_token)
                    clear_current_chat()
                    st.rerun()
                except ChatAPIError as error:
                    st.error(str(error))

    if save_clicked:
        try:
            with st.spinner("상담 내용을 핵심만 요약하고 있습니다..."):
                if not st.session_state.get(SAVE_REQUEST_KEY):
                    st.session_state[SAVE_REQUEST_KEY] = str(uuid4())
                response = save_chat_summary(st.session_state.access_token, request_id=st.session_state[SAVE_REQUEST_KEY])
            st.session_state.pop("ai-chat-summary-cache", None)
            clear_current_chat()
            st.session_state[MESSAGE_KEY] = (response.get("data") or {}).get("remaining_messages") or []
            st.session_state[FLASH_KEY] = response.get(
                "message", "상담 요약 미리보기를 저장했습니다."
            )
            st.rerun()
        except ChatAPIError as error:
            st.error(str(error))
