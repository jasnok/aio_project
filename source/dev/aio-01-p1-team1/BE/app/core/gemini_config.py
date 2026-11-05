"""Gemini 설정과 클라이언트를 챗봇 호출 시점에 준비합니다.

기존 FastAPI 기능은 Gemini 설정이 없어도 계속 실행될 수 있도록 import 시점에는
API key를 검사하지 않습니다. 로컬 화면 검증은 CHAT_GEMINI_MODE=mock으로 동작합니다.
"""

from __future__ import annotations

from app.core.settings import get_setting

# 프런트엔드의 상담 대기 45초 안에서 오류를 안내합니다. 값은 밀리초입니다.
GEMINI_HTTP_TIMEOUT_MS = 30_000


def get_chat_setting(name: str, default: str = "") -> str:
    return get_setting(name, default)


def get_gemini_mode() -> str:
    """mock 또는 gemini 중 현재 실행 모드를 반환합니다."""

    mode = get_chat_setting("CHAT_GEMINI_MODE", "mock").lower()
    if mode not in {"mock", "gemini"}:
        raise RuntimeError("CHAT_GEMINI_MODE는 mock 또는 gemini여야 합니다.")
    return mode


def get_gemini_model() -> str:
    return get_chat_setting("GEMINI_MODEL", "gemini-2.5-flash-lite")


def get_history_limit() -> int:
    raw_value = get_chat_setting("CHAT_HISTORY_LIMIT", "10")
    try:
        return max(0, min(int(raw_value), 30))
    except ValueError as error:
        raise RuntimeError("CHAT_HISTORY_LIMIT는 정수여야 합니다.") from error


def get_gemini_client():
    """실제 Gemini 모드에서만 API key를 검사하고 클라이언트를 만듭니다."""

    api_key = get_chat_setting("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your-"):
        raise RuntimeError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    from google import genai
    from google.genai import types

    return genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=GEMINI_HTTP_TIMEOUT_MS,
        retry_options=types.HttpRetryOptions(attempts=1),
    ))
