"""백엔드(FastAPI) API에서 공통으로 사용하는 HTTP 요청 기능입니다."""
from typing import Any

import httpx
import streamlit as st
from core.settings import settings
from housing_common.http_response import decode_response

def _get_backend_url() -> str:
    """세 앱이 공유하는 설정 우선순위로 백엔드 주소를 읽습니다."""
    return settings.http_url("BACKEND_URL", "http://127.0.0.1:8000")


BACKEND_URL = _get_backend_url()
REQUEST_TIMEOUT = 15.0


class BackendAPIError(Exception):
    """백엔드 연결 또는 API 응답 처리 중 발생한 오류입니다."""


def request(
    method: str,
    path: str,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
):
    if params is not None:
        # httpx가 None 값을 빈 문자열로 보내면 백엔드 쿼리 파라미터 검증이 실패하므로 제거합니다.
        params = {key: value for key, value in params.items() if value is not None}

    try:
        token = st.session_state.get("access_token", "")
        response = httpx.request(
            method,
            f"{BACKEND_URL}{path}",
            json=json,
            params=params,
            headers={"Authorization": f"Bearer {token}"} if token else None,
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.TimeoutException as error:
        raise BackendAPIError("백엔드 응답 시간이 초과되었습니다.") from error
    except httpx.RequestError as error:
        raise BackendAPIError(
            "백엔드 서버에 연결할 수 없습니다. 서버 실행 상태를 확인해 주세요."
        ) from error

    return decode_response(response, BackendAPIError)
