"""호텔 검색 입력 스키마."""

from typing import Literal

from pydantic import Field, field_validator

from .common import StrictInputModel, StrictOutputModel


class SearchHotelsInput(StrictInputModel):
    region: str = Field(min_length=1, max_length=50)
    max_price: int | None = Field(default=None, ge=1)
    count: int = Field(default=5, ge=1, le=20)
    query: str = Field(default="", max_length=500)

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if not value:
            raise ValueError("region은 빈 문자열일 수 없습니다.")
        return value


class HotelItem(StrictOutputModel):
    hotel_id: str
    name: str
    city: str
    district: str | None = None
    address: str | None = None
    price: int
    rating: float | None = None
    review_count: int | None = None
    hotel_grade: int | str | None = None
    room_type: str | None = None
    breakfast_included: bool | None = None
    parking: bool | None = None
    wifi: bool | None = None
    pool: bool | None = None
    description: str | None = None
    similarity: float | None = None
    proximity_level: Literal["same_area", "same_city"] | None = None


class HotelSearchFilters(StrictOutputModel):
    region: str
    max_price: int | None
    query: str | None


class SearchHotelsOutput(StrictOutputModel):
    items: list[HotelItem]
    count: int = Field(ge=0)
    requested_count: int = Field(ge=1, le=20)
    filters: HotelSearchFilters
    sort: Literal["similarity_desc_then_price_asc", "price_asc"]
    search_mode: Literal["vector", "structured", "structured_fallback"]
    source: Literal["local-pgvector"]
