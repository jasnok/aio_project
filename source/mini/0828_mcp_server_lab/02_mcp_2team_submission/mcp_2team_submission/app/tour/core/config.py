"""Tour MCP 환경설정을 한곳에서 관리합니다."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PACKAGE_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    mcp_host: str = os.getenv("TOUR_MCP_HOST", "127.0.0.1")
    mcp_port: int = int(os.getenv("TOUR_MCP_PORT", "8020"))
    database_url: str = os.getenv("DATABASE_URL", "").strip()
    embedding_provider: str = os.getenv("TOUR_EMBEDDING_PROVIDER", "openai").lower()
    openai_embedding_model: str = os.getenv(
        "OPENAI_EMBEDDING_MODEL",
        os.getenv("TOUR_EMBEDDING_MODEL", "text-embedding-3-small"),
    )
    openai_embedding_dimensions: int = int(os.getenv(
        "OPENAI_EMBEDDING_DIMENSIONS",
        os.getenv("TOUR_EMBEDDING_DIMENSIONS", "1536"),
    ))
    ollama_base_url: str = os.getenv(
        "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
    ).rstrip("/")
    ollama_embedding_model: str = os.getenv(
        "OLLAMA_EMBEDDING_MODEL", "embeddinggemma"
    )
    ollama_request_timeout_seconds: float = float(os.getenv(
        "OLLAMA_REQUEST_TIMEOUT_SECONDS", "120"
    ))


settings = Settings()
