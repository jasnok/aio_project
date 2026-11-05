"""Supabase에서 회원 데이터를 처리합니다."""

import base64
import hashlib
import secrets
from typing import Any

from app.core.database_errors import is_unique_violation
from app.core.id_generator import generate_time_id
from app.core.supabase_client import get_supabase
from app.schemas.user_schema import UserCreate, UserPublic, UserUpdate


PUBLIC_COLUMNS = "user_id,email,name,created_at,updated_at"


class UserServiceError(Exception):
    """회원 DB 처리 실패를 Router에 안전하게 전달합니다."""


class DuplicateEmailError(UserServiceError):
    """중복 이메일을 별도의 409 응답으로 변환하기 위한 오류입니다."""


def _hash_password(password: str) -> str:
    """비밀번호를 PBKDF2-HMAC-SHA256 해시로 변환합니다."""

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return "pbkdf2_sha256$600000$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def _to_public(row: dict[str, Any]) -> UserPublic:
    return UserPublic.model_validate(row)


def user_create(user: UserCreate) -> UserPublic:
    try:
        result = (
            get_supabase()
            .table("users")
            .insert(
                {
                    "user_id": generate_time_id(),
                    "email": user.email,
                    "password": _hash_password(user.password),
                    "name": user.name,
                }
            )
            .execute()
        )
        if not result.data:
            raise UserServiceError
        return _to_public(result.data[0])
    except UserServiceError:
        raise
    except Exception as exc:
        if is_unique_violation(exc):
            raise DuplicateEmailError from exc
        raise UserServiceError from exc


def user_get_all() -> list[UserPublic]:
    try:
        result = get_supabase().table("users").select(PUBLIC_COLUMNS).execute()
        return [_to_public(row) for row in result.data]
    except Exception as exc:
        raise UserServiceError from exc


def user_get(user_id: str) -> UserPublic | None:
    try:
        result = get_supabase().table("users").select(PUBLIC_COLUMNS).eq("user_id", user_id).limit(1).execute()
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise UserServiceError from exc


def user_update(user_id: str, user: UserUpdate) -> UserPublic | None:
    try:
        result = (
            get_supabase()
            .table("users")
            .update({"email": user.email, "password": _hash_password(user.password), "name": user.name})
            .eq("user_id", user_id)
            .execute()
        )
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        if is_unique_violation(exc):
            raise DuplicateEmailError from exc
        raise UserServiceError from exc


def user_delete(user_id: str) -> UserPublic | None:
    try:
        result = get_supabase().table("users").delete().eq("user_id", user_id).execute()
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise UserServiceError from exc
