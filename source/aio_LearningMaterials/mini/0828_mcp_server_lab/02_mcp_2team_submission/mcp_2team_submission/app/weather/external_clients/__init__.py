"""Weather MCP가 사용하는 외부 API 클라이언트입니다."""

from .kma_client import request_forecast

__all__ = ["request_forecast"]
