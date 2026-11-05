from typing import Literal

from pydantic import Field

from .common import StrictInputModel, StrictOutputModel


class SearchHotelPoliciesInput(StrictInputModel):
    hotel_ids: list[str] = Field(min_length=1, max_length=5)
    question: str = Field(min_length=1, max_length=300)
    top_k_per_hotel: int = Field(default=2, ge=1, le=3)


class HotelPolicyMatch(StrictOutputModel):
    policy_id: int
    hotel_id: str
    hotel_name: str
    policy_type: str
    title: str
    content: str
    effective_date: str
    similarity: float | None = None
    is_mock: bool


class SearchHotelPoliciesOutput(StrictOutputModel):
    question: str
    items: list[HotelPolicyMatch]
    count: int = Field(ge=0)
    search_mode: Literal["vector", "structured_fallback"]
    embedding_provider: str | None = None
    embedding_model: str | None = None
    mock_data_notice: str
