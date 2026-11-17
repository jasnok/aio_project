"""Gemini Chat 요청 및 응답 모델입니다."""

from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("메시지는 비어 있을 수 없습니다.")
        return normalized


class ChatResponse(BaseModel):
    answer: str
    model: str
