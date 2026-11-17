"""Supabase에서 게시글 데이터를 처리합니다."""

from typing import Any

from app.core.id_generator import generate_time_id
from app.core.supabase_client import get_supabase
from app.schemas.post_schema import PostCreate, PostPublic, PostUpdate


PUBLIC_COLUMNS = "post_id,user_id,title,content,created_at,updated_at"


class PostServiceError(Exception):
    """게시글 DB 처리 실패입니다."""


class PostAuthorNotFoundError(PostServiceError):
    """게시글 작성자를 찾을 수 없습니다."""


def _to_public(row: dict[str, Any]) -> PostPublic:
    return PostPublic.model_validate(row)


def _user_exists(user_id: str) -> bool:
    result = get_supabase().table("users").select("user_id").eq("user_id", user_id).limit(1).execute()
    return bool(result.data)


def post_create(post: PostCreate) -> PostPublic:
    try:
        if not _user_exists(post.user_id):
            raise PostAuthorNotFoundError
        result = (
            get_supabase()
            .table("posts")
            .insert(
                {
                    "post_id": generate_time_id(),
                    "user_id": post.user_id,
                    "title": post.title,
                    "content": post.content,
                }
            )
            .execute()
        )
        if not result.data:
            raise PostServiceError
        return _to_public(result.data[0])
    except (PostAuthorNotFoundError, PostServiceError):
        raise
    except Exception as exc:
        raise PostServiceError from exc


def post_get_all() -> list[PostPublic]:
    try:
        result = get_supabase().table("posts").select(PUBLIC_COLUMNS).order("created_at", desc=True).execute()
        return [_to_public(row) for row in result.data]
    except Exception as exc:
        raise PostServiceError from exc


def post_get(post_id: str) -> PostPublic | None:
    try:
        result = get_supabase().table("posts").select(PUBLIC_COLUMNS).eq("post_id", post_id).limit(1).execute()
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise PostServiceError from exc


def post_update(post_id: str, post: PostUpdate) -> PostPublic | None:
    try:
        result = (
            get_supabase()
            .table("posts")
            .update({"title": post.title, "content": post.content})
            .eq("post_id", post_id)
            .execute()
        )
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise PostServiceError from exc


def post_delete(post_id: str) -> PostPublic | None:
    try:
        result = get_supabase().table("posts").delete().eq("post_id", post_id).execute()
        return _to_public(result.data[0]) if result.data else None
    except Exception as exc:
        raise PostServiceError from exc
