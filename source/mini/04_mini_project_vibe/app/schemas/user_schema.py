"""회원 요청값 검증과 공개 응답 모델입니다."""

from datetime import datetime
import re

from pydantic import BaseModel, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class UserCreate(BaseModel):
    email: str = Field(max_length=254, examples=["user@example.com"])
    password: str = Field(max_length=128, examples=["safe-password"])
    name: str = Field(max_length=100, examples=["홍길동"])

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("이메일은 example@example.com 형식으로 입력해 주세요.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("비밀번호는 8자 이상 입력해 주세요.")
        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("이름은 공백을 제외하고 1자 이상 입력해 주세요.")
        return normalized


class UserUpdate(UserCreate):
    """PUT 전체 수정은 생성과 같은 필드를 받습니다."""


class UserPublic(BaseModel):
    """비밀번호를 제외하고 외부에 공개하는 회원 정보입니다."""

    user_id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
