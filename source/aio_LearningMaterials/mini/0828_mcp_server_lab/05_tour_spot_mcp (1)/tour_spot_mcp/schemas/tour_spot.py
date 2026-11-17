"""관광지 검색 결과로 반환하는 데이터 형식입니다."""

from pydantic import BaseModel, Field


class TourSpot(BaseModel):
    content_id: str
    name: str
    address: str | None = None
    image_url: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class TourSpotSearchResult(BaseModel):
    location: str
    resolved_location: str | None = None
    count: int = Field(ge=0)
    items: list[TourSpot]
    source: str = "한국관광공사 국문 관광정보 서비스"
    message: str | None = None
