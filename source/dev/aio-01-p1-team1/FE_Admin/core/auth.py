"""공통 로그인 상태와 인증 동작을 관리합니다."""

import streamlit as st

from clients.admin_client import login_process
from core.api_client import BackendAPIError


def init_state(
    stored_loginout: str = "logout",
    stored_admin_username: str = "",
    stored_admin_token: str = "",
) -> None:
    st.session_state.setdefault("loginout", stored_loginout)
    st.session_state.setdefault("admin_username", stored_admin_username)
    st.session_state.setdefault("admin_token", stored_admin_token)


def login(username: str, password: str) -> None:
    try:
        result = login_process(username, password)
        if result.get("success"):
            token = result["data"].get("access_token") or ""
            if not token:
                st.error("관리자 인증 정보가 없습니다. 다시 로그인해 주세요.")
                return
            st.session_state.loginout = "login"
            st.session_state.admin_username = result["data"]["username"]
            st.session_state.admin_token = token
            st.rerun()
        else:
            st.error(result.get("message", "로그인에 실패했습니다."))
    except BackendAPIError as error:
        st.error(str(error))


def logout() -> None:
    st.session_state.loginout = "logout"
    st.session_state.admin_username = ""
    st.session_state.admin_token = ""


def is_logged_in() -> bool:
    return st.session_state.loginout == "login" and bool(st.session_state.get("admin_token"))
