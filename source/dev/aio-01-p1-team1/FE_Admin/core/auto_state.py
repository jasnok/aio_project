import streamlit as st

def store_analysis(extracted, source_name, images, labels, mode):
    """새 분석을 열 때 이전 문서의 수정값과 선택을 함께 초기화합니다."""
    for key in list(st.session_state):
        if str(key).startswith(("auto-fix-", "auto-pick-", "auto-imgpick-", "auto-shared-")):
            del st.session_state[key]
    st.session_state.auto_extracted = extracted
    st.session_state.auto_source_name = source_name
    st.session_state.auto_images = images
    st.session_state.auto_image_labels = labels
    st.session_state.auto_fixes = {}
    st.session_state.auto_shared = {}
    st.session_state.auto_result_mode = mode
    st.session_state.auto_registered = set()

