"""공고 변경과 사진의 업로드·저장·정리 순서를 관리합니다."""
from fastapi import HTTPException, UploadFile
from app.core.api_response import ApiResponse
from app.core.upload_config import MAX_IMAGE_COUNT
from app.schemas.listing_schema import ListingCreate
from app.services.image_service import delete_listing_image, upload_listing_image, upload_listing_images
from app.services.listing_service import listing_get, listing_update, listing_clear_image, listing_delete

async def update_listing(listing_id: int, validated: ListingCreate, image: UploadFile | None = None, remove_image: bool = False) -> ApiResponse:
    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    has_new_image = image is not None and bool(image.filename)

    # 새로 올리면서 동시에 지우라는 요청은 뜻이 서로 어긋나므로 받지 않습니다.
    if has_new_image and remove_image:
        raise HTTPException(
            status_code=400,
            detail="새 이미지 업로드와 기존 이미지 삭제를 함께 선택할 수 없습니다.",
        )

    # 이미지는 세 가지 중 하나입니다.
    #   새 파일이 오면        -> 대표 이미지 교체
    #   지우라고 하면         -> 대표 이미지 없음
    #   둘 다 아니면          -> 그대로 유지
    #
    # 대표 이미지 말고 다른 사진은 여기서 건드리지 않습니다.
    # 이 API는 제목·금액을 저장하는 곳이고, 사진 목록 관리는
    # PUT /admin/listings/{id}/images 가 따로 맡습니다.
    # 여기서 사진 목록을 비워 보내면 수정을 저장할 때마다
    # 추가 사진이 전부 사라집니다.
    others = [url for url in current_listing.images if url != current_listing.image_url]

    if has_new_image:
        image_url = await upload_listing_image(image)
        image_urls = [image_url] + others
    elif remove_image:
        # 대표를 지우면 남은 사진 중 첫 장이 대표가 됩니다.
        image_urls = others
        image_url = image_urls[0] if image_urls else None
    else:
        image_url = current_listing.image_url
        image_urls = list(current_listing.images)

    listing = validated.model_copy(update={"image_url": image_url, "image_urls": image_urls})
    try:
        updated_listing = listing_update(listing_id, listing)
    except Exception:
        if has_new_image:
            delete_listing_image(image_url)
        raise

    if updated_listing is None:
        # DB 수정이 실패했는데 새 이미지를 이미 올렸다면, 쓰이지 않는 파일이 되므로 지웁니다.
        # 기존 이미지는 아직 공고가 쓰고 있으므로 건드리지 않습니다.
        if has_new_image:
            delete_listing_image(image_url)
        raise HTTPException(status_code=500, detail="청약정보 수정에 실패했습니다.")

    # DB 수정이 끝난 뒤에만 예전 이미지를 지웁니다.
    if image_url != current_listing.image_url:
        delete_listing_image(current_listing.image_url)

    return ApiResponse(
        success=True,
        message="청약정보가 수정되었습니다.",
        data=updated_listing,
    )


def remove_listing_image(listing_id: int) -> ApiResponse:
    """공고는 그대로 두고 이미지만 지웁니다.

    수정 API와 따로 둔 이유는, 관리자가 화면에 입력만 해 두고 아직 저장하지 않은
    제목·금액 같은 값이 이미지를 지울 때 함께 저장되지 않도록 하기 위해서입니다.
    이 API는 공고 id만 받고 다른 값은 받지 않습니다.
    """

    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    # 이미 이미지가 없으면 지울 것이 없습니다. 여러 번 눌러도 여기서 끝납니다.
    if not current_listing.image_url:
        return ApiResponse(
            success=True,
            message="이미 이미지가 없는 청약정보입니다.",
            data=current_listing,
        )

    updated_listing = listing_clear_image(listing_id)
    if updated_listing is None:
        # DB가 아직 기존 이미지를 가리키고 있으므로 파일을 지우면 공고가 깨집니다.
        raise HTTPException(status_code=500, detail="이미지 삭제에 실패했습니다.")

    # DB에서 참조를 지운 뒤에만 파일을 지웁니다.
    # 외부 URL·공유 이미지 제외와 실패 기록은 image_service가 맡습니다.
    delete_listing_image(current_listing.image_url)

    return ApiResponse(
        success=True,
        message="이미지를 삭제했습니다.",
        data=updated_listing,
    )


async def replace_listing_images(listing_id: int, keep_count: int, kept_image_urls: list[str], images: list[UploadFile]) -> ApiResponse:
    """공고의 사진 목록을 새로 씁니다.

    수정 API와 따로 둔 이유는 이미지 삭제 API(4-1)와 같습니다.
    관리자가 화면에 입력만 해 두고 아직 저장하지 않은 제목·금액 같은 값이
    사진을 정리할 때 함께 저장되지 않도록 하기 위해서입니다.

    남길 사진(kept_image_urls)에 새로 올린 사진을 이어 붙인 것이
    최종 목록이 됩니다. 첫 장이 대표 이미지가 됩니다.

    keep_count는 "남길 사진이 몇 장인지" 화면이 함께 알려 주는 값입니다.
    이 값을 반드시 받도록 한 이유가 있습니다.
    보내는 형식이 조금만 틀려도 kept_image_urls가 통째로 사라지는데,
    그러면 서버는 "남길 사진 없음"으로 알아듣고 사진을 전부 지웁니다.
    실제로 그렇게 사진 열 장이 한 번에 사라진 적이 있습니다.
    장수를 함께 받아 맞춰 보면, 값이 사라진 요청은 지우기 전에 걸러집니다.
    """

    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    # 화면이 말한 장수와 실제로 도착한 장수가 다르면 중간에 값이 샌 것입니다.
    # 이때 그냥 진행하면 남겨야 할 사진까지 지웁니다.
    if keep_count != len(kept_image_urls):
        raise HTTPException(
            status_code=400,
            detail=f"남길 사진 목록이 온전하지 않습니다. "
            f"({keep_count}장이라고 했는데 {len(kept_image_urls)}장이 도착했습니다) "
            f"아무것도 지우지 않았습니다.",
        )

    # 화면이 엉뚱한 URL을 보내도 이 공고의 사진만 남깁니다.
    current_images = list(current_listing.images)
    kept = [url for url in kept_image_urls if url in current_images]

    # 기존 데이터도 먼저 검증하여 업로드 후 입력 오류가 나는 경우를 막습니다.
    validated = ListingCreate(**current_listing.model_dump(
        exclude={"id", "created_at", "image_url", "images", "image_urls"}
    ))

    uploaded = await upload_listing_images(images)
    image_urls = kept + uploaded

    if len(image_urls) > MAX_IMAGE_COUNT:
        # 방금 올린 파일은 아직 아무도 쓰지 않으므로 도로 지웁니다.
        for image_url in uploaded:
            delete_listing_image(image_url)
        raise HTTPException(
            status_code=400,
            detail=f"사진은 최대 {MAX_IMAGE_COUNT}장까지 붙일 수 있습니다. "
            f"(남길 사진 {len(kept)}장 + 새 사진 {len(uploaded)}장)",
        )

    listing = validated.model_copy(update={
        "image_url": image_urls[0] if image_urls else None, "image_urls": image_urls,
    })
    try:
        updated_listing = listing_update(listing_id, listing)
    except Exception:
        for image_url in uploaded:
            delete_listing_image(image_url)
        raise

    if updated_listing is None:
        for image_url in uploaded:
            delete_listing_image(image_url)
        raise HTTPException(status_code=500, detail="사진 저장에 실패했습니다.")

    # DB가 새 목록을 가리키게 된 뒤에만 빠진 사진의 파일을 지웁니다.
    for image_url in current_images:
        if image_url not in image_urls:
            delete_listing_image(image_url)

    return ApiResponse(
        success=True,
        message=f"사진 {len(image_urls)}장을 저장했습니다.",
        data=updated_listing,
    )


def delete_listing(listing_id: int) -> ApiResponse:
    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    # 지우기 전에 사진 목록을 먼저 읽어 둡니다.
    # listing_images 행은 공고와 함께 사라지므로(ON DELETE CASCADE),
    # 지운 뒤에는 어떤 파일을 지워야 하는지 알 수 없습니다.
    image_urls = list(current_listing.images)

    # 대표 이미지가 목록에 빠져 있어도 반드시 지웁니다.
    # 빠뜨리면 아무도 안 쓰는 파일이 Storage에 영영 남습니다.
    if current_listing.image_url and current_listing.image_url not in image_urls:
        image_urls.append(current_listing.image_url)

    deleted_listing = listing_delete(listing_id)
    if deleted_listing is None:
        raise HTTPException(status_code=500, detail="청약정보 삭제에 실패했습니다.")

    # 공고를 지운 뒤 Storage에 남은 이미지 파일도 함께 지웁니다.
    # 다른 공고가 같은 파일을 쓰고 있으면 image_service가 걸러 냅니다.
    for image_url in image_urls:
        delete_listing_image(image_url)

    return ApiResponse(
        success=True,
        message="청약정보가 삭제되었습니다.",
        data=deleted_listing,
    )


