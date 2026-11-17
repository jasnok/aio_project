"""호텔 MCP Tool 진입 함수."""

from ..schemas import (
    RecommendHotelsInput,
    RecommendHotelsOutput,
    SearchHotelsInput,
    SearchHotelsOutput,
)
from ..services import hotel_service, recommendation_service


def search_hotels(
    region: str, max_price: int | None = None, count: int = 5, query: str = ""
) -> dict:
    """지역·선택적 최대 가격으로 호텔을 검색하며 count 기본값은 5입니다."""
    result = hotel_service.search(SearchHotelsInput(
        region=region, max_price=max_price, count=count, query=query
    ))
    return SearchHotelsOutput.model_validate(result).model_dump(mode="json")


def recommend_hotels_near_attraction(
    attraction_name: str,
    max_price: int | None = None,
    count: int = 5,
    query: str = "",
) -> dict:
    """관광지와 같은 구역·도시의 호텔을 우선순위에 따라 추천합니다."""
    result = recommendation_service.recommend(RecommendHotelsInput(
        attraction_name=attraction_name, max_price=max_price,
        count=count, query=query,
    ))
    return RecommendHotelsOutput.model_validate(result).model_dump(
        mode="json", exclude_none=True
    )
