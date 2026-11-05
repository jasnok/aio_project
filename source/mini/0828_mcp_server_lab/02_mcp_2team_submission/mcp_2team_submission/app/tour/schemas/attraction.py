"""관광지 검색과 호텔 추천 입력 스키마."""

from typing import Literal

from pydantic import Field, field_validator

from .common import StrictInputModel, StrictOutputModel
from .hotel import HotelItem


class SearchAttractionsInput(StrictInputModel):
    region: str = Field(min_length=1, max_length=50)
    count: int = Field(default=5, ge=1, le=20)
    query: str = Field(default="", max_length=500)

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if not value:
            raise ValueError("region은 빈 문자열일 수 없습니다.")
        return value


class RecommendHotelsInput(StrictInputModel):
    attraction_name: str = Field(min_length=1, max_length=100)
    max_price: int | None = Field(default=None, ge=1)
    count: int = Field(default=5, ge=1, le=20)
    query: str = Field(default="", max_length=500)

    @field_validator("attraction_name")
    @classmethod
    def validate_attraction_name(cls, value: str) -> str:
        if not value:
            raise ValueError("attraction_name은 빈 문자열일 수 없습니다.")
        return value


class AttractionItem(StrictOutputModel):
    id: int | str
    city: str
    area: str
    name: str
    address: str | None = None
    description: str | None = None
    precautions: list[str] | str | None = None
    similarity: float | None = None


class AttractionSearchFilters(StrictOutputModel):
    region: str
    query: str | None


class SearchAttractionsOutput(StrictOutputModel):
    items: list[AttractionItem]
    count: int = Field(ge=0)
    requested_count: int = Field(ge=1, le=20)
    filters: AttractionSearchFilters
    search_mode: Literal["vector", "structured", "structured_fallback"]
    source: Literal["local-pgvector"]


class AttractionCandidate(StrictOutputModel):
    id: int | str
    city: str
    area: str
    name: str
    address: str | None = None
    description: str | None = None


class RecommendationFilters(StrictOutputModel):
    max_price: int | None
    query: str | None


class RecommendHotelsOutput(StrictOutputModel):
    status: Literal["ok", "not_found", "ambiguous_attraction"]
    source: Literal["local-pgvector"]
    attraction: AttractionCandidate | None = None
    hotels: list[HotelItem] = Field(default_factory=list)
    candidates: list[AttractionCandidate] = Field(default_factory=list)
    count: int = Field(default=0, ge=0)
    requested_count: int | None = Field(default=None, ge=1, le=20)
    filters: RecommendationFilters | None = None
    message: str | None = None
    matching_basis: Literal["same_area_then_same_city"] | None = None
    search_mode: Literal["vector", "structured"] | None = None
    distance_notice: str | None = None
