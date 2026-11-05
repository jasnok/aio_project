"""여행 MCP 입력 스키마."""

from .attraction import (
    RecommendHotelsInput,
    RecommendHotelsOutput,
    SearchAttractionsInput,
    SearchAttractionsOutput,
)
from .hotel import SearchHotelsInput, SearchHotelsOutput
from .policy import SearchHotelPoliciesInput, SearchHotelPoliciesOutput

__all__ = [
    "RecommendHotelsInput",
    "RecommendHotelsOutput",
    "SearchAttractionsInput",
    "SearchAttractionsOutput",
    "SearchHotelsInput",
    "SearchHotelsOutput",
    "SearchHotelPoliciesInput",
    "SearchHotelPoliciesOutput",
]
