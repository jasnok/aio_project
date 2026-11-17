from ..models.requests import SpotSearchRequest


def register_spot_tools(mcp, service):
    @mcp.tool()
    async def search_spots(city: str, category: str | None = None, keyword: str | None = None) -> dict:
        """도시·카테고리·검색어 조건으로 관광지를 조회합니다."""
        request = SpotSearchRequest(city=city, category=category, keyword=keyword)
        return await service.search_spots(request.city, request.category, request.keyword)

    return search_spots
