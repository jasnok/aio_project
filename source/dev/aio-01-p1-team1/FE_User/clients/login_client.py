"""관리자 인증 성공 때만 관리자 화면으로 이동합니다."""
import httpx
from core.api_client import BACKEND_URL, BackendAPIError
from housing_common.http_response import decode_response


def admin_handoff(username: str, password: str) -> str | None:
    try:
        response = httpx.post(BACKEND_URL + "/login-handoff/admin", json={"username": username, "password": password}, timeout=15)
    except httpx.RequestError as error:
        raise BackendAPIError("로그인 서버에 연결할 수 없습니다.") from error
    if response.status_code == 401:
        return None
    return decode_response(response, BackendAPIError)["data"]["ticket"]
