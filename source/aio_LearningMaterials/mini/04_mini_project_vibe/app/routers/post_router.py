"""게시글 CRUD HTTP API입니다."""

from fastapi import APIRouter, HTTPException, status

from app.core.api_response import ApiResponse
from app.schemas.post_schema import PostCreate, PostUpdate
from app.services.post_service import (
    PostAuthorNotFoundError,
    PostServiceError,
    post_create,
    post_delete,
    post_get,
    post_get_all,
    post_update,
)


post_router = APIRouter(prefix="/posts", tags=["Post"])


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="게시글 정보를 처리하는 중 오류가 발생했습니다.")


@post_router.post("", status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate) -> ApiResponse:
    try:
        data = post_create(post)
    except PostAuthorNotFoundError:
        raise HTTPException(status_code=404, detail="작성자를 찾을 수 없습니다.") from None
    except PostServiceError:
        raise _database_error() from None
    return ApiResponse(success=True, message="게시글이 생성되었습니다.", data=data)


@post_router.get("")
def get_posts() -> ApiResponse:
    try:
        data = post_get_all()
    except PostServiceError:
        raise _database_error() from None
    return ApiResponse(success=True, message="게시글 목록을 조회했습니다.", data=data)


@post_router.get("/{post_id}")
def get_post(post_id: str) -> ApiResponse:
    try:
        data = post_get(post_id)
    except PostServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="게시글을 조회했습니다.", data=data)


@post_router.put("/{post_id}")
def update_post(post_id: str, post: PostUpdate) -> ApiResponse:
    try:
        data = post_update(post_id, post)
    except PostServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="게시글이 수정되었습니다.", data=data)


@post_router.delete("/{post_id}")
def delete_post(post_id: str) -> ApiResponse:
    try:
        data = post_delete(post_id)
    except PostServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return ApiResponse(success=True, message="게시글이 삭제되었습니다.", data=data)
