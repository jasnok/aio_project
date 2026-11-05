"""환경변수를 읽어 공통 Supabase Client를 생성합니다."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def get_required_env(name: str) -> str:
    """필수 환경변수가 없거나 예시 값이면 이해하기 쉬운 오류를 냅니다."""

    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} 환경변수가 설정되지 않았습니다.")
    if value.startswith(("your_", "your-", "https://your-")):
        raise RuntimeError(f"{name} 환경변수가 예시 값입니다.")
    return value


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """프로세스에서 재사용할 Supabase Client를 한 번 생성합니다."""

    load_dotenv(ENV_PATH)
    url = get_required_env("SUPABASE_URL")
    service_role_key = get_required_env("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, service_role_key)
