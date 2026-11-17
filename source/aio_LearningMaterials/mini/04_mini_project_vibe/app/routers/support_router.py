"""고객 문의 CRUD HTTP API입니다."""

from fastapi import APIRouter, HTTPException, status

from app.core.api_response import ApiResponse
from app.schemas.support_schema import SupportCreate, SupportUpdate
from app.services.support_service import (
    SupportAuthorNotFoundError,
    SupportServiceError,
    support_create,
    support_delete,
    support_get,
    support_get_all,
    support_update,
)


support_router = APIRouter(prefix="/supports", tags=["Support"])


def _database_error() -> HTTPException:
    return HTTPException(status_code=500, detail="문의 정보를 처리하는 중 오류가 발생했습니다.")


@support_router.post("", status_code=status.HTTP_201_CREATED)
def create_support(support: SupportCreate) -> ApiResponse:
    try:
        data = support_create(support)
    except SupportAuthorNotFoundError:
        raise HTTPException(status_code=404, detail="작성자를 찾을 수 없습니다.") from None
    except SupportServiceError:
        raise _database_error() from None
    return ApiResponse(success=True, message="문의가 생성되었습니다.", data=data)


@support_router.get("")
def get_supports() -> ApiResponse:
    try:
        data = support_get_all()
    except SupportServiceError:
        raise _database_error() from None
    return ApiResponse(success=True, message="문의 목록을 조회했습니다.", data=data)


@support_router.get("/{support_id}")
def get_support(support_id: str) -> ApiResponse:
    try:
        data = support_get(support_id)
    except SupportServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")
    return ApiResponse(success=True, message="문의를 조회했습니다.", data=data)


@support_router.put("/{support_id}")
def update_support(support_id: str, support: SupportUpdate) -> ApiResponse:
    try:
        data = support_update(support_id, support)
    except SupportServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")
    return ApiResponse(success=True, message="문의가 수정되었습니다.", data=data)


@support_router.delete("/{support_id}")
def delete_support(support_id: str) -> ApiResponse:
    try:
        data = support_delete(support_id)
    except SupportServiceError:
        raise _database_error() from None
    if data is None:
        raise HTTPException(status_code=404, detail="문의를 찾을 수 없습니다.")
    return ApiResponse(success=True, message="문의가 삭제되었습니다.", data=data)
