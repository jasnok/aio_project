from ..models.requests import HotelSearchRequest


def register_hotel_tools(mcp, service):
    @mcp.tool()
    async def search_hotels(city: str, max_price: int | None = None, keyword: str | None = None) -> dict:
        """도시와 가격·검색어 조건으로 호텔을 조회합니다."""
        request = HotelSearchRequest(city=city, max_price=max_price, keyword=keyword)
        return await service.search_hotels(request.city, request.max_price, request.keyword)

    return search_hotels
