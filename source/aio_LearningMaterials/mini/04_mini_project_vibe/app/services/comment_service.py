"""Supabase에서 댓글 데이터를 처리합니다."""

from typing import Any

from app.core.id_generator import generate_time_id
from app.core.supabase_client import get_supabase
from app.schemas.comment_schema import CommentCreate, CommentPublic, CommentUpdate


PUBLIC_COLUMNS = "comment_id,post_id,user_id,content,created_at,updated_at"


class CommentServiceError(Exception):
    """댓글 DB 처리 실패입니다."""


class CommentPostNotFoundError(CommentServiceError):
    """댓글을 작성할 게시글이 없습니다."""


class CommentAuthorNotFoundError(CommentServiceError):
    """댓글 작성자가 없습니다."""


def _to_public(row: dict[str, Any]) -> CommentPublic:
    return CommentPublic.model_validate(row)


def _record_exists(table: str, column: str, value: str) -> bool:
    result = get_supabase().table(table).select(column).eq(column, value).limit(1).execute()
    return bool(result.data)


def comment_create(post_id: str, comment: CommentCreate) -> CommentPublic:
    try:
        if not _record_exists("posts", "post_id", post_id):
            raise CommentPostNotFoundError
        if not _record_exists("users", "user_id", comment.user_id):
            raise CommentAuthorNotFoundError
        result = (
            get_supabase()
            .table("comments")
            .insert(
                {
                    "comment_id": generate_time_id(),
                    "post_id": post_id,
                    "user_id": comment.user_id,
                    "content": comment.content,
                }
            )
            .execute()
        )
        if not result.data:
            raise CommentServiceError
        return _to_public(result.data[0])
    except (CommentPostNotFoundError, CommentAuthorNotFoundError, CommentServiceError):
        raise
    except Exception as exc:
        raise CommentServiceError from exc


def comment_get_all() -> list[CommentPublic]:
    try:
        result = get_supabase().table("comments").select(PUBLIC_COLUMNS).order("created_at", desc=True).execute()
        return [_to_public(row) for row in result.data]
    except Exception as exc:
        raise CommentServiceError from exc


def comment_get_by_post(post_id: str) -> list[CommentPublic] | None:
    try:
        if not _record_exists("posts", "post_id", post_id):
            return None
        result = (
            get_supabase()
            .table("comments")
            .select(PUBLIC_COLUMNS)
            .eq("post_id", post_id)
            .order("created_at")
            .execute()
        )
        return [_to_public(row) for row in result.data]
    except Exception as exc:
        raise CommentServiceError from exc


def comment_get(comment_id: str) -> CommentPublic | None:
    try:
        result = (
            get_supabase().table("comments").select(PUBLIC_COLUMNS).eq("comment_id", comment_id).limit(1).execute()
        )
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise CommentServiceError from exc


def comment_update(comment_id: str, comment: CommentUpdate) -> CommentPublic | None:
    try:
        result = (
            get_supabase()
            .table("comments")
            .update({"content": comment.content})
            .eq("comment_id", comment_id)
            .execute()
        )
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise CommentServiceError from exc


def comment_delete(comment_id: str) -> CommentPublic | None:
    try:
        result = get_supabase().table("comments").delete().eq("comment_id", comment_id).execute()
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise CommentServiceError from exc
