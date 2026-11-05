"""호텔과 관광지 DB 행을 임베딩용 검색 문서로 변환합니다."""


def build_hotel_content(hotel: dict) -> str:
    facilities = [
        label
        for field, label in (
            ("breakfast_included", "조식"),
            ("parking", "주차"),
            ("wifi", "와이파이"),
            ("pool", "수영장"),
        )
        if hotel.get(field)
    ]
    return "\n".join([
        f"호텔명: {hotel['name']}",
        f"지역: {hotel['city']} {hotel.get('district') or ''}".strip(),
        f"주소: {hotel.get('address') or ''}",
        f"가격: {hotel['price']}원",
        f"등급: {hotel.get('hotel_grade') or '미등록'}성급",
        f"객실 유형: {hotel.get('room_type') or '미등록'}",
        f"평점: {hotel.get('rating') or '미등록'}",
        f"편의시설: {', '.join(facilities) or '등록된 편의시설 없음'}",
        f"설명: {hotel.get('description') or ''}",
    ])


def build_attraction_content(attraction: dict) -> str:
    precautions = attraction.get("precautions") or []
    return "\n".join([
        f"관광지명: {attraction['name']}",
        f"지역: {attraction['city']} {attraction['area']}",
        f"주소: {attraction['address']}",
        f"설명: {attraction['description']}",
        f"주의사항: {' '.join(precautions)}",
    ])


def build_hotel_policy_content(policy: dict) -> str:
    return "\n".join([
        f"호텔명: {policy['hotel_name']}",
        f"정책 유형: {policy['policy_type']}",
        f"정책 제목: {policy['title']}",
        f"규정: {policy['content']}",
        f"시행일: {policy['effective_date']}",
        "안내: 프로젝트 검증을 위해 생성한 임의 정책",
    ])
