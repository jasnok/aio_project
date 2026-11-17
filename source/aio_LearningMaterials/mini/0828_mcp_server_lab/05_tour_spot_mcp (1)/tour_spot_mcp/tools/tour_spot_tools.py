"""관광지 검색 기능을 MCP Tool로 공개합니다."""

from mcp.server.fastmcp import FastMCP

from services import TourSpotService


def register_tour_spot_tools(mcp: FastMCP, service: TourSpotService) -> None:
    @mcp.tool()
    def search_tour_spots(location: str, limit: int = 5) -> dict:
        """대한민국 국내 지역의 관광지를 검색합니다.

        Args:
            location: 부산, 제주, 강릉, 경북 경주처럼 검색할 국내 지역명입니다.
            limit: 반환할 관광지 개수이며 1~10 범위입니다.
        """
        result = service.search(location=location, limit=limit)
        return result.model_dump(mode="json")
