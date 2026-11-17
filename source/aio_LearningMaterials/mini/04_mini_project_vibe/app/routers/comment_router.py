"""댓글 CRUD HTTP API입니다."""

from fastapi import APIRouter, HTTPException, status

from app.core.api_response import ApiResponse
from app.schemas.comment_schema import CommentCreate, CommentUpdate
from app.services.comment_service import (
    CommentAuthorNotFoundError,
    CommentPostNotFoundError,
    CommentServiceError,
    comment_create,
    comment_delete,
    comment_get,
    comment_get_all,
    comment_get_by_post,
    comment_update,
)


comment_router = APIRouter(tags=["Comment"])


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="댓글 정보를 처리하는 중 오류가 발생했습니다.")


@comment_router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(post_id: str, comment: CommentCreate) -> ApiResponse:
    try:
        data = comment_create(post_id, comment)
    except CommentPostNotFoundError:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.") from None
    except CommentAuthorNotFoundError:
        raise HTTPException(status_code=404, detail="작성자를 찾을 수 없습니다.") from None
    except CommentServiceError:
        raise _database_error() from None
    return ApiResponse(success=True, message="댓글이 생성되었습니다.", data=data)


@comment_router.get("/comments")
def get_comments() -> ApiResponse:
    try:
        data = comment_get_all()
    except CommentServiceError:
        raise _database_error() from None
    return ApiResponse(success=True, message="댓글 목록을 조회했습니다.", data=data)


@comment_router.get("/posts/{post_id}/comments")
def get_post_comments(post_id: str) -> ApiResponse:
    try:
        data = comment_get_by_post(post_id)
    except CommentServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="게시글 댓글을 조회했습니다.", data=data)


@comment_router.get("/comments/{comment_id}")
def get_comment(comment_id: str) -> ApiResponse:
    try:
        data = comment_get(comment_id)
    except CommentServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="댓글을 조회했습니다.", data=data)


@comment_router.put("/comments/{comment_id}")
def update_comment(comment_id: str, comment: CommentUpdate) -> ApiResponse:
    try:
        data = comment_update(comment_id, comment)
    except CommentServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="댓글이 수정되었습니다.", data=data)


@comment_router.delete("/comments/{comment_id}")
def delete_comment(comment_id: str) -> ApiResponse:
    try:
        data = comment_delete(comment_id)
    except CommentServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="댓글이 삭제되었습니다.", data=data)
