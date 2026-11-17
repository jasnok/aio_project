"""모든 API에서 공통으로 사용하는 응답 모델입니다."""

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """성공 여부와 안내 문구, 실제 응답 데이터를 담습니다."""

    success: bool
    message: str
    data: Any | None = None
