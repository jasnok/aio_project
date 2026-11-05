"""AI 상담 API 요청과 응답 모델입니다."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_CHAT_MESSAGE_LENGTH = 4000


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_CHAT_MESSAGE_LENGTH)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("메시지는 비어 있을 수 없습니다.")
        return cleaned


class ChatHistorySnapshot(BaseModel):
    """Redis 내부 상태. revision은 모델 문맥과 API 응답에 포함하지 않습니다."""
    revision: UUID | None = None
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    messages: list[ChatMessage] = Field(default_factory=list, max_length=100)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("질문을 입력해 주세요.")
        return cleaned


class ChatAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=MAX_CHAT_MESSAGE_LENGTH)
    model: str
    history_count: int = Field(ge=0)

    @field_validator("answer")
    @classmethod
    def answer_must_fit_history(cls, value: str) -> str:
        return ChatMessage(role="assistant", content=value).content


class ChatSummaryDraft(BaseModel):
    """AI가 생성하는 값만 검증합니다. 사용자 ID·저장 ID는 서버가 추가합니다."""

    model_config = ConfigDict(strict=True, extra="forbid")
    title: str = ""
    summary: str = Field(min_length=1)

    @field_validator("title", "summary", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChatSaveRequest(BaseModel):
    # 이전 프런트엔드와의 호환을 위해 필드는 유지하지만 Redis 기록을 기준으로 저장합니다.
    messages: list[ChatMessage] = Field(default_factory=list, max_length=100)
    request_id: UUID | None = None


class ChatSummaryItem(BaseModel):
    id: UUID
    user_id: str
    title: str
    summary: str
    message_count: int
    model: str
    created_at: datetime


class ChatSummarySaveResult(ChatSummaryItem):
    # 요약 생성 중 대화가 변경됐다면 화면이 기존 기록을 지우지 않도록 전달합니다.
    remaining_messages: list[ChatMessage] = Field(default_factory=list)


class ChatProfile(BaseModel):
    user_id: str
    nickname: str
    email: str
