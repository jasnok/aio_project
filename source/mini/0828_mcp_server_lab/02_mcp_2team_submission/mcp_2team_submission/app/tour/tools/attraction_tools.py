"""관광지 MCP Tool 진입 함수."""

from ..schemas import SearchAttractionsInput, SearchAttractionsOutput
from ..services import attraction_service


def search_tourist_attractions(
    region: str, count: int = 5, query: str = ""
) -> dict:
    """지역으로 대한민국 관광지를 검색하며 count 기본값은 5입니다."""
    result = attraction_service.search(
        SearchAttractionsInput(region=region, count=count, query=query)
    )
    return SearchAttractionsOutput.model_validate(result).model_dump(mode="json")
