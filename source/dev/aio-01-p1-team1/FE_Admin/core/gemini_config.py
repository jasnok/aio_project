"""관리자 Gemini도 공통 설정 규칙을 사용합니다. 비밀값은 출력하지 않습니다."""

from housing_config import is_placeholder, read_env_file
from core.settings import get_setting, settings

DEFAULT_MODEL = "gemini-2.5-flash"


def get_api_key() -> str:
    value = get_setting("GEMINI_API_KEY")
    return "" if is_placeholder(value) else value


def get_model_name() -> str:
    return get_setting("GEMINI_MODEL", DEFAULT_MODEL)


def has_api_key() -> bool:
    return bool(get_api_key())
