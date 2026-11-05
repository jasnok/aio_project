"""Gemini API에 필요한 환경변수를 제공합니다."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_gemini_api_key() -> str:
    """Gemini API Key가 없으면 안전한 설정 오류를 냅니다."""

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    return api_key


def get_gemini_model() -> str:
    """코드에 모델명을 고정하지 않고 환경변수에서 읽습니다."""

    model = os.getenv("GEMINI_MODEL", "").strip()
    if not model:
        raise RuntimeError("GEMINI_MODEL 환경변수가 설정되지 않았습니다.")
    return model
