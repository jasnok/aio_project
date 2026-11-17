"""Weather MCP 환경설정을 한곳에서 관리합니다."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PACKAGE_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    mcp_host: str = os.getenv("MCP_HOST", "127.0.0.1")
    mcp_port: int = int(os.getenv("MCP_PORT", "8013"))
    kma_api_key: str = unquote(os.getenv("KMA_API_KEY", ""))
    kma_api_base_url: str = os.getenv(
        "KMA_API_BASE_URL",
        "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0",
    ).rstrip("/")
    kma_api_version: str = os.getenv("KMA_API_VERSION", "2.0")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))

    def validate(self) -> None:
        parsed = urlparse(self.kma_api_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("KMA_API_BASE_URL은 유효한 HTTP(S) URL이어야 합니다.")


settings = Settings()
settings.validate()
