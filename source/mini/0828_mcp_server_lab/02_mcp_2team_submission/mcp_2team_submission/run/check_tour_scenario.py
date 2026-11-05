"""부산 호텔 검색 → 해당 호텔 정책 RAG 흐름을 실제 MCP 호출로 점검합니다."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "backend" / ".env")


def payload(result) -> dict:
    if result.isError:
        raise RuntimeError("MCP Tool 실행 실패")
    if result.structuredContent:
        value = result.structuredContent
        return value.get("result", value)
    for block in result.content:
        text = getattr(block, "text", None)
        if text:
            return json.loads(text)
    raise RuntimeError("MCP Tool 결과가 비어 있습니다.")


async def main() -> None:
    url = os.getenv("TOUR_MCP_URL", "http://127.0.0.1:8020/mcp")
    async with streamable_http_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            hotel_result = await session.call_tool(
                "search_hotels",
                {
                    "region": "부산",
                    "max_price": 120000,
                    "count": 3,
                    "query": "2일 여행 가성비 호텔",
                },
            )
            hotels = payload(hotel_result)
            items = hotels.get("items", [])
            if not items or any(item["price"] > 120000 for item in items):
                raise RuntimeError("부산 12만 원 이하 호텔 검색 결과가 올바르지 않습니다.")

            hotel_ids = [item["hotel_id"] for item in items]
            policy_result = await session.call_tool(
                "search_hotel_policies",
                {
                    "hotel_ids": hotel_ids,
                    "question": "당일 취소와 환불 규정을 알려줘",
                    "top_k_per_hotel": 1,
                },
            )
            policies = payload(policy_result)
            if not policies.get("items"):
                raise RuntimeError("호텔 정책 검색 결과가 없습니다.")
            if policies.get("embedding_provider") != "ollama":
                raise RuntimeError("정책 벡터 검색이 Ollama를 사용하지 않았습니다.")
            if any(item["hotel_id"] not in hotel_ids for item in policies["items"]):
                raise RuntimeError("검색하지 않은 호텔의 정책이 포함됐습니다.")

            print(json.dumps({
                "hotels": [
                    {"hotel_id": item["hotel_id"], "name": item["name"], "price": item["price"]}
                    for item in items
                ],
                "policy_count": policies["count"],
                "policy_search_mode": policies["search_mode"],
                "embedding_provider": policies["embedding_provider"],
                "embedding_model": policies["embedding_model"],
            }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
