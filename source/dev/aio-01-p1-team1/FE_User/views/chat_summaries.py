"""저장된 상담 요약 조회·삭제 화면입니다."""
import streamlit as st
from clients.chat_client import ChatAPIError, get_chat_summaries, delete_chat_summary
from core.session_result import session_result
from core.chat_state import (
    FLASH_KEY,
    SUMMARY_SELECTED_KEY,
    SUMMARY_DELETE_CONFIRM_KEY,
    SUMMARY_RESET_KEY,
)


def show_saved_summaries() -> None:
    # Streamlit 위젯이 생성되기 전에 이전 실행에서 예약한 초기화를 처리합니다.
    if st.session_state.get(SUMMARY_RESET_KEY):
        st.session_state[SUMMARY_SELECTED_KEY] = None
        st.session_state[SUMMARY_RESET_KEY] = False

    with st.container(border=True):
        st.markdown("#### 저장된 상담")
        if st.button("상담 목록 새로고침"):
            st.session_state.pop("ai-chat-summary-cache", None)
        try:
            response = session_result(
                st.session_state, "ai-chat-summary-cache",
                (st.session_state.user_id, st.session_state.access_token),
                lambda: get_chat_summaries(st.session_state.access_token),
            )
            summaries = response.get("data") or []
        except ChatAPIError as error:
            st.warning(f"저장된 상담을 불러오지 못했습니다: {error}")
            return

        if not summaries:
            st.caption("저장된 상담 요약이 없습니다.")
            return

        summary_by_id = {str(item.get("id")): item for item in summaries}
        if st.session_state.get(SUMMARY_SELECTED_KEY) not in summary_by_id:
            st.session_state[SUMMARY_SELECTED_KEY] = None
        select_col, delete_col = st.columns([9, 1], vertical_alignment="bottom")
        with select_col:
            selected_id = st.selectbox(
                "확인할 상담",
                options=list(summary_by_id),
                index=None,
                placeholder="상담을 선택하세요",
                key=SUMMARY_SELECTED_KEY,
                format_func=lambda item_id: (
                    f"{summary_by_id[item_id].get('title') or '제목 없는 상담'} · "
                    f"{str(summary_by_id[item_id].get('created_at') or '').replace('T', ' ')[:19]}"
                ),
            )
        with delete_col:
            if st.button(
                "✕",
                key="delete_selected_summary",
                help="선택한 상담 삭제",
                disabled=not selected_id,
                use_container_width=True,
            ):
                st.session_state[SUMMARY_DELETE_CONFIRM_KEY] = selected_id
                st.rerun()

        delete_target = st.session_state.get(SUMMARY_DELETE_CONFIRM_KEY)
        if delete_target and delete_target in summary_by_id:
            st.warning("선택한 상담 요약을 삭제할까요? 삭제한 내용은 복구할 수 없습니다.")
            cancel_col, confirm_col = st.columns(2)
            with cancel_col:
                if st.button("삭제 취소", use_container_width=True):
                    st.session_state[SUMMARY_DELETE_CONFIRM_KEY] = None
                    st.rerun()
            with confirm_col:
                if st.button("삭제 확인", type="primary", use_container_width=True):
                    try:
                        response = delete_chat_summary(
                            delete_target,
                            st.session_state.access_token,
                        )
                        st.session_state.pop("ai-chat-summary-cache", None)
                        st.session_state[SUMMARY_DELETE_CONFIRM_KEY] = None
                        st.session_state[SUMMARY_RESET_KEY] = True
                        st.session_state[FLASH_KEY] = response.get(
                            "message", "저장된 상담을 삭제했습니다."
                        )
                        st.rerun()
                    except ChatAPIError as error:
                        st.error(str(error))

        if selected_id:
            item = summary_by_id[selected_id]
            st.write(item.get("summary") or "요약 내용이 없습니다.")
            st.caption(
                f"메시지 {item.get('message_count', 0)}개 · model={item.get('model', '-') }"
            )
