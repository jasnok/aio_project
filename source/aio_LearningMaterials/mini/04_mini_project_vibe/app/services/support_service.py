"""Supabase에서 고객 문의 데이터를 처리합니다."""

from typing import Any

from app.core.id_generator import generate_time_id
from app.core.supabase_client import get_supabase
from app.schemas.support_schema import SupportCreate, SupportPublic, SupportUpdate


PUBLIC_COLUMNS = "support_id,user_id,title,content,status,created_at,updated_at"


class SupportServiceError(Exception):
    """고객 문의 DB 처리 실패입니다."""


class SupportAuthorNotFoundError(SupportServiceError):
    """문의 작성자가 없습니다."""


def _to_public(row: dict[str, Any]) -> SupportPublic:
    return SupportPublic.model_validate(row)


def _user_exists(user_id: str) -> bool:
    result = get_supabase().table("users").select("user_id").eq("user_id", user_id).limit(1).execute()
    return bool(result.data)


def support_create(support: SupportCreate) -> SupportPublic:
    try:
        if not _user_exists(support.user_id):
            raise SupportAuthorNotFoundError
        result = (
            get_supabase()
            .table("supports")
            .insert(
                {
                    "support_id": generate_time_id(),
                    "user_id": support.user_id,
                    "title": support.title,
                    "content": support.content,
                    "status": support.status.value,
                }
            )
            .execute()
        )
        if not result.data:
            raise SupportServiceError
        return _to_public(result.data[0])
    except (SupportAuthorNotFoundError, SupportServiceError):
        raise
    except Exception as exc:
        raise SupportServiceError from exc


def support_get_all() -> list[SupportPublic]:
    try:
        result = get_supabase().table("supports").select(PUBLIC_COLUMNS).order("created_at", desc=True).execute()
        return [_to_public(row) for row in result.data]
    except Exception as exc:
        raise SupportServiceError from exc


def support_get(support_id: str) -> SupportPublic | None:
    try:
        result = (
            get_supabase().table("supports").select(PUBLIC_COLUMNS).eq("support_id", support_id).limit(1).execute()
        )
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise SupportServiceError from exc


def support_update(support_id: str, support: SupportUpdate) -> SupportPublic | None:
    try:
        result = (
            get_supabase()
            .table("supports")
            .update({"title": support.title, "content": support.content, "status": support.status.value})
            .eq("support_id", support_id)
            .execute()
        )
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise SupportServiceError from exc


def support_delete(support_id: str) -> SupportPublic | None:
    try:
        result = get_supabase().table("supports").delete().eq("support_id", support_id).execute()
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise SupportServiceError from exc
