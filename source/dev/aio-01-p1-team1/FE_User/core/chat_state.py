"""사용자별 상담 세션 초기화와 종료 상태를 관리합니다."""
import streamlit as st

MESSAGE_KEY = "ai_chat_messages"
OWNER_KEY = "ai_chat_owner_id"
NICKNAME_KEY = "ai_chat_nickname"
END_CONFIRM_KEY = "ai_chat_end_confirm"
FLASH_KEY = "ai_chat_flash"
ERROR_KEY = "ai_chat_error"
SAVE_REQUEST_KEY = "ai_chat_save_request_id"
HISTORY_ATTEMPTED_KEY = "ai_chat_history_attempted"
HISTORY_READY_KEY = "ai_chat_history_ready"
SUMMARY_SELECTED_KEY = "ai_chat_selected_summary"
SUMMARY_DELETE_CONFIRM_KEY = "ai_chat_summary_delete_confirm"
SUMMARY_RESET_KEY = "ai_chat_summary_reset"


def clear_current_chat() -> None:
    st.session_state[MESSAGE_KEY] = []
    st.session_state[END_CONFIRM_KEY] = False
    st.session_state.pop(SAVE_REQUEST_KEY, None)


def initialize_chat_state() -> None:
    current_user_id = st.session_state.user_id
    if st.session_state.get(OWNER_KEY) != current_user_id:
        st.session_state.pop(SAVE_REQUEST_KEY, None)
        st.session_state.pop("ai-chat-summary-cache", None)
        st.session_state.pop("ai-chat-profile-cache", None)
        st.session_state.pop(FLASH_KEY, None)
        st.session_state.pop(ERROR_KEY, None)
        st.session_state[OWNER_KEY] = current_user_id
        st.session_state[HISTORY_ATTEMPTED_KEY] = False
        st.session_state[HISTORY_READY_KEY] = False
        st.session_state[MESSAGE_KEY] = []
        st.session_state[NICKNAME_KEY] = "회원"
        st.session_state[END_CONFIRM_KEY] = False
        st.session_state[SUMMARY_SELECTED_KEY] = None
        st.session_state[SUMMARY_DELETE_CONFIRM_KEY] = None
        st.session_state[SUMMARY_RESET_KEY] = False
    else:
        st.session_state.setdefault(HISTORY_ATTEMPTED_KEY, False)
        st.session_state.setdefault(HISTORY_READY_KEY, False)
        st.session_state.setdefault(MESSAGE_KEY, [])
        st.session_state.setdefault(NICKNAME_KEY, "회원")
        st.session_state.setdefault(END_CONFIRM_KEY, False)
        st.session_state.setdefault(SUMMARY_SELECTED_KEY, None)
        st.session_state.setdefault(SUMMARY_DELETE_CONFIRM_KEY, None)
        st.session_state.setdefault(SUMMARY_RESET_KEY, False)
