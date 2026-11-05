# admin_router.py
from datetime import date
from decimal import Decimal
from typing import Annotated
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.core.api_response import ApiResponse
from app.core.admin_auth import TOKEN_LIFETIME, create_admin_token, get_current_admin
from app.schemas.admin_schema import AdminLogin
from app.schemas.listing_schema import ListingCreate
from app.services.admin_service import admin_login_process
from app.services import listing_mutations
from app.services.favorite_service import favorite_detail, favorite_ranking
from app.services.image_service import upload_listing_image, upload_listing_images
from app.services.listing_service import (
    listing_create,
)

admin_login_router = APIRouter(prefix="/admin", tags=["Admin"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"],
                         dependencies=[Depends(get_current_admin)])

# 200: 정상 - 정상 실행 되면 자동 전송
# 401: 로그인 실패
# 404: 데이터 없음
# 500: 서버 또는 DB 처리 실패

# 1. 관리자 로그인
@admin_login_router.post("/login")
def login(admin: AdminLogin) -> ApiResponse:
    logged_in_admin = admin_login_process(admin)
    token = create_admin_token(logged_in_admin)
    return ApiResponse(
        success=True,
        message="관리자 로그인에 성공했습니다.",
        data={**logged_in_admin.model_dump(mode="json"), "access_token": token,
              "expires_in": int(TOKEN_LIFETIME.total_seconds())},
    )


# 2. 청약정보 등록
@admin_router.post("/listings/create")
def create_listing(listing: ListingCreate) -> ApiResponse:
    created_listing = listing_create(listing)
    if created_listing is None:
        raise HTTPException(status_code=500, detail="청약정보 등록에 실패했습니다.")
    return ApiResponse(
        success=True,
        message="청약정보가 등록되었습니다.",
        data=created_listing,
    )


# 3. 청약정보 이미지 업로드
@admin_router.post("/listings/images")
async def create_listing_image(
    image: Annotated[UploadFile, File()],
) -> ApiResponse:
    image_url = await upload_listing_image(image)
    return ApiResponse(
        success=True,
        message="이미지를 업로드했습니다.",
        data={"image_url": image_url},
    )


# 3-1. 청약정보 이미지 여러 장 업로드
#      한 장짜리(3번)는 그대로 두어 기존 호출이 계속 동작하게 합니다.
@admin_router.post("/listings/images/bulk")
async def create_listing_images(
    images: Annotated[list[UploadFile], File()],
) -> ApiResponse:
    """사진을 한 번에 올리고 공개 URL을 순서대로 돌려줍니다.

    한 장이라도 실패하면 이미 올라간 파일을 도로 지웁니다.
    화면은 여기서 받은 URL 목록을 공고 등록·수정에 그대로 넘깁니다.
    """

    image_urls = await upload_listing_images(images)
    return ApiResponse(
        success=True,
        message=f"이미지 {len(image_urls)}장을 업로드했습니다.",
        data={"image_urls": image_urls},
    )


# 4. 청약정보 수정
@admin_router.put("/listings/update/{listing_id}")
async def update_listing(
    listing_id: int,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    housing_name: Annotated[str, Form(min_length=1, max_length=255)],
    area_sqm: Annotated[Decimal, Form(gt=0)],
    recruitment_count: Annotated[int, Form(gt=0)],
    location: Annotated[str, Form(min_length=1, max_length=50)],
    deposit: Annotated[int, Form(ge=0)],
    monthly_rent: Annotated[int, Form(ge=0)],
    application_start_date: Annotated[date, Form()],
    application_end_date: Annotated[date, Form()],
    description: Annotated[str, Form(min_length=1)],
    source_url: Annotated[str, Form(min_length=1)],
    detail_address: Annotated[str | None, Form(max_length=255)] = None,
    image: Annotated[UploadFile | None, File()] = None,
    remove_image: Annotated[bool, Form()] = False,
) -> ApiResponse:
    # 상세주소를 비워서 보내면 빈 문자열 대신 값 없음으로 저장합니다.
    detail_address = (detail_address or "").strip() or None

    # Validate all fields before uploading anything to Storage.
    try:
        validated = ListingCreate(
            title=title, housing_name=housing_name, area_sqm=area_sqm,
            recruitment_count=recruitment_count, location=location,
            detail_address=detail_address, deposit=deposit, monthly_rent=monthly_rent,
            application_start_date=application_start_date,
            application_end_date=application_end_date, description=description,
            source_url=source_url,
        )
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error

    return await listing_mutations.update_listing(listing_id, validated, image, remove_image)


# 4-1. 청약정보 이미지만 삭제
@admin_router.delete("/listings/{listing_id}/image")
def remove_listing_image(listing_id: int) -> ApiResponse:
    return listing_mutations.remove_listing_image(listing_id)


# 4-2. 청약정보 사진 목록 통째로 저장
@admin_router.put("/listings/{listing_id}/images")
async def replace_listing_images(
    listing_id: int,
    keep_count: Annotated[int, Form(ge=0)],
    kept_image_urls: Annotated[list[str], Form()] = [],
    images: Annotated[list[UploadFile], File()] = [],
) -> ApiResponse:
    return await listing_mutations.replace_listing_images(listing_id, keep_count, kept_image_urls, images)


# 5. 청약정보 삭제
@admin_router.delete("/listings/delete/{listing_id}")
def delete_listing(listing_id: int) -> ApiResponse:
    return listing_mutations.delete_listing(listing_id)


# 6. 즐겨찾기 많은 순 조회
@admin_router.get("/favorites/ranking")
def get_favorite_ranking() -> ApiResponse:
    ranking = favorite_ranking()
    return ApiResponse(
        success=True,
        message="즐겨찾기 순위를 조회했습니다.",
        data=ranking,
    )


# 7. 어떤 유저가 어떤 청약정보를 즐겨찾기했는지 조회
@admin_router.get("/favorites/detail")
def get_favorite_detail(listing_id: int | None = Query(default=None)) -> ApiResponse:
    details = favorite_detail(listing_id)
    return ApiResponse(
        success=True,
        message="즐겨찾기 상세 내역을 조회했습니다.",
        data=details,
    )
