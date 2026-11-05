"""8013 포트에서 독립 실행되는 여행투어 Streamable HTTP MCP Server입니다."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# 0.0.0.0: 이 컴퓨터의 모든 네트워크 인터페이스(loopback 포함)에서 리슨합니다.
# 실제 바인딩/접속 주소는 .env의 MCP_HOST / TOUR_MCP_URL로 제어하세요. 여기 코드는 건드리지 마세요.
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("TOUR_MCP_PORT", "8013"))

MAX_HOTEL_PRICE = 150_000

mcp = FastMCP(
    "mini-agent-tour",
    instructions="호텔과 인기 여행 스팟을 제공하는 교육용 여행투어 서버입니다.",
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,
    json_response=True,
)

# 실습용 고정 카탈로그입니다. 실제로는 여기 대신 DB 조회나 외부 API 호출로 교체합니다.
_HOTELS = [
    {
        "hotel_id": "hotel-busan-001",
        "name": "바다 호텔",
        "location": "부산",
        "price": 120_000,
    },
    {
        "hotel_id": "hotel-seoul-001",
        "name": "도시 호텔",
        "location": "서울",
        "price": 140_000,
    },
]

_POPULAR_SPOTS = {
    "부산": [
        {"spot_id": "spot-busan-001", "name": "해운대 해수욕장", "category": "해변", "popularity_rank": 1},
        {"spot_id": "spot-busan-002", "name": "감천문화마을", "category": "문화마을", "popularity_rank": 2},
        {"spot_id": "spot-busan-003", "name": "광안리 해수욕장", "category": "해변", "popularity_rank": 3},
    ],
    "서울": [
        {"spot_id": "spot-seoul-001", "name": "경복궁", "category": "고궁", "popularity_rank": 1},
        {"spot_id": "spot-seoul-002", "name": "명동", "category": "쇼핑", "popularity_rank": 2},
        {"spot_id": "spot-seoul-003", "name": "남산타워", "category": "전망", "popularity_rank": 3},
    ],
}


@mcp.tool()
def search_hotels(
    location: Literal["부산", "서울"],
    max_price: int = MAX_HOTEL_PRICE,
) -> dict:
    """위치와 1박 최대 가격(기본/상한 150,000원)으로 호텔을 검색합니다."""
    normalized = location.strip()
    if not normalized:
        raise ValueError("location은 빈 문자열일 수 없습니다.")
    if max_price < 1:
        raise ValueError("max_price는 1 이상이어야 합니다.")
    if max_price > MAX_HOTEL_PRICE:
        raise ValueError(f"max_price는 {MAX_HOTEL_PRICE}원을 초과할 수 없습니다.")

    return {
        "items": [
            hotel for hotel in _HOTELS
            if hotel["location"] == normalized and hotel["price"] <= max_price
        ],
        "source": "tour-hotel-catalog",
    }


@mcp.tool()
def search_popular_spots(
    location: Literal["부산", "서울"],
    limit: int = 3,
) -> dict:
    """위치 기준으로 사람들이 많이 찾는 인기 여행 스팟을 조회합니다."""
    normalized = location.strip()
    if not normalized:
        raise ValueError("location은 빈 문자열일 수 없습니다.")
    if limit < 1:
        raise ValueError("limit은 1 이상이어야 합니다.")

    spots = sorted(_POPULAR_SPOTS[normalized], key=lambda spot: spot["popularity_rank"])
    return {
        "location": normalized,
        "items": spots[:limit],
        "source": "tour-spot-catalog",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
