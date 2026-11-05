"""서버가 검색한 생활권 공고 후보의 표시 이름입니다."""


def listing_label(listing: dict) -> str:
    """검색된 공고를 선택 목록에 표시할 문자열을 만듭니다."""

    title = str(listing.get("title") or "공고명 없음")
    housing_name = str(listing.get("housing_name") or "")
    detail_address = str(
        listing.get("detail_address") or "상세주소 없음"
    )

    display_name = housing_name or title

    return f"{display_name} | {detail_address}"
