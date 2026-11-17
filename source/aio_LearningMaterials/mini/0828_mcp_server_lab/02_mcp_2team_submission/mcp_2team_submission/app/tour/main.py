"""대한민국 호텔·관광지 Streamable HTTP MCP 서버."""

from mcp.server.fastmcp import FastMCP

from .core.config import settings
from .tools.attraction_tools import search_tourist_attractions
from .tools.hotel_tools import recommend_hotels_near_attraction, search_hotels
from .tools.policy_tools import search_hotel_policies


mcp = FastMCP(
    "mini-agent-tour",
    instructions=(
        "대한민국 내 호텔과 관광지 명소 정보를 제공합니다. "
        "지역, 가격 및 자연어 조건으로 호텔과 관광지를 검색하며, "
        "관광지 주변 호텔을 추천할 수 있습니다."
        "호텔 검색 결과의 hotel_id로 데모 취소·환불 정책을 검색할 수 있습니다."
    ),
    host=settings.mcp_host,
    port=settings.mcp_port,
    stateless_http=True,
    json_response=True,
)

mcp.tool()(search_hotels)
mcp.tool()(search_tourist_attractions)
mcp.tool()(recommend_hotels_near_attraction)
mcp.tool()(search_hotel_policies)


@mcp.resource("tour://guide/korea")
def korea_tour_guide() -> str:
    """대한민국 호텔 및 관광지 검색 서비스 안내입니다."""
    return (
        "대한민국 내 호텔과 관광지 명소 정보를 제공합니다. "
        "가격을 지정하지 않은 호텔 검색은 낮은 가격순으로 최대 5개를 반환합니다. "
        "자연어 조건은 pgvector 유사도 검색에 사용합니다. "
        "관광지 주변 호텔은 현재 동일 행정구역과 도시를 기준으로 추천합니다."
    )


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
