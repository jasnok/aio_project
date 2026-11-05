"""고객 문의 요청값 검증과 공개 응답 모델입니다."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class SupportStatus(StrEnum):
    PENDING = "pending"
    ANSWERED = "answered"
    CLOSED = "closed"


class SupportCreate(BaseModel):
    user_id: str = Field(min_length=17, max_length=17)
    title: str = Field(max_length=200)
    content: str
    status: SupportStatus = SupportStatus.PENDING

    @field_validator("title", "content")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("문의 제목과 내용은 비어 있을 수 없습니다.")
        return normalized


class SupportUpdate(BaseModel):
    title: str = Field(max_length=200)
    content: str
    status: SupportStatus

    @field_validator("title", "content")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("문의 제목과 내용은 비어 있을 수 없습니다.")
        return normalized


class SupportPublic(BaseModel):
    support_id: str
    user_id: str
    title: str
    content: str
    status: SupportStatus
    created_at: datetime
    updated_at: datetime
