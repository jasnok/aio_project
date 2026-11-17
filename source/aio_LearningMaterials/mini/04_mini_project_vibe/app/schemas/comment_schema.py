"""댓글 요청값 검증과 공개 응답 모델입니다."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CommentCreate(BaseModel):
    user_id: str = Field(min_length=17, max_length=17)
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("댓글 내용은 비어 있을 수 없습니다.")
        return normalized


class CommentUpdate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("댓글 내용은 비어 있을 수 없습니다.")
        return normalized


class CommentPublic(BaseModel):
    comment_id: str
    post_id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: datetime
