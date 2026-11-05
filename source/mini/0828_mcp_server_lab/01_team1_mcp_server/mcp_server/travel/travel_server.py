"""8010 포트에서 독립 실행되는 여행 Streamable HTTP MCP Server입니다."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# 0.0.0.0: 이 컴퓨터의 모든 네트워크 인터페이스(loopback 포함)에서 리슨합니다.
# 실제 바인딩/접속 주소는 .env의 MCP_HOST / TRAVEL_MCP_URL로 제어하세요. 여기 코드는 건드리지 마세요.
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("TRAVEL_MCP_PORT", "8010"))

mcp = FastMCP(
    "mini-agent-travel",
    instructions="현재 날씨와 여행 정책을 제공하는 교육용 서버입니다.",
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,
    json_response=True,
)


# @mcp.tool()
# def get_current_weather(city: Literal["부산", "서울"]) -> dict:
#     """도시의 현재 날씨를 조회합니다."""
#     normalized = city.strip()
#     if not normalized:
#         raise ValueError("city는 빈 문자열일 수 없습니다.")
#     return {
#         "city": normalized,
#         "condition": "맑음",
#         "temperature_c": 24,
#         "source": "travel-weather-service",
#     }


@mcp.resource("travel://policy/baggage")
def baggage_policy() -> str:
    """교육용 국내선 수하물 정책입니다."""
    return "교육용 국내선의 위탁 수하물은 15kg까지 허용합니다."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
