"""실행 중인 두 Streamable HTTP MCP 서버의 Tool 발견을 확인합니다."""

import asyncio
import os
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "backend" / ".env")


async def tool_names(url: str) -> list[str]:
    async with streamable_http_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.list_tools()
            return [tool.name for tool in response.tools]


async def main() -> None:
    tour_url = os.getenv("TOUR_MCP_URL", "http://127.0.0.1:8020/mcp")
    weather_url = os.getenv("WEATHER_MCP_URL", "http://127.0.0.1:8013/mcp")
    tour = await tool_names(tour_url)
    weather = await tool_names(weather_url)
    expected_tour = {
        "search_hotels",
        "recommend_hotels_near_attraction",
        "search_tourist_attractions",
        "search_hotel_policies",
    }
    expected_weather = {"get_current_weather", "get_next_week_weather"}
    missing_tour = expected_tour.difference(tour)
    missing_weather = expected_weather.difference(weather)
    if missing_tour or missing_weather:
        raise RuntimeError(
            f"MCP Tool 누락: tour={sorted(missing_tour)}, "
            f"weather={sorted(missing_weather)}"
        )
    print({"tour": tour, "weather": weather})


if __name__ == "__main__":
    asyncio.run(main())
