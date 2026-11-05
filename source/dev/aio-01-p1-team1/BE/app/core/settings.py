"""백엔드 설정의 단일 진입점입니다."""

from pathlib import Path

from housing_config import Settings

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
settings = Settings(ENV_PATH)
get_setting = settings.get


def get_allowed_origins() -> list[str]:
    default = "http://localhost:8501,http://localhost:8502,http://127.0.0.1:8501,http://127.0.0.1:8502"
    return [item.strip() for item in get_setting("ALLOWED_ORIGINS", default).split(",") if item.strip()]
