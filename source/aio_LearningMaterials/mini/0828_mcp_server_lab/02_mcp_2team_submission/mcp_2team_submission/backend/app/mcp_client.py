"""Tour와 Weather MCP 서버에 Streamable HTTP로 연결합니다."""

import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=True)

MCP_SERVERS: dict[str, dict[str, str]] = {
    "tour": {
        "transport": "streamable-http",
        "url": os.getenv("TOUR_MCP_URL", "http://127.0.0.1:8020/mcp"),
    },
    "weather": {
        "transport": "streamable-http",
        "url": os.getenv("WEATHER_MCP_URL", "http://127.0.0.1:8013/mcp"),
    },
}


async def open_session(
    stack: AsyncExitStack,
    config: dict[str, str],
) -> ClientSession:
    """Streamable HTTP 연결을 열고 초기화된 MCP Session을 반환합니다."""
    read_stream, write_stream, _ = await stack.enter_async_context(
        streamable_http_client(config["url"])
    )
    session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    return session


@asynccontextmanager
async def mcp_session(server_name: str) -> AsyncIterator[ClientSession]:
    """지정한 MCP 서버 하나에 연결합니다."""
    config = MCP_SERVERS.get(server_name)
    if config is None:
        raise ValueError(f"등록되지 않은 MCP Server입니다: {server_name}")
    async with AsyncExitStack() as stack:
        yield await open_session(stack, config)


@asynccontextmanager
async def mcp_sessions() -> AsyncIterator[dict[str, ClientSession]]:
    """Agent 실행에 필요한 Tour와 Weather MCP Session을 함께 엽니다."""
    async with AsyncExitStack() as stack:
        sessions = {
            name: await open_session(stack, config)
            for name, config in MCP_SERVERS.items()
        }
        yield sessions


def result_text(result) -> str:
    return "\n".join(
        content.text for content in result.content if hasattr(content, "text")
    )


async def discover_tools() -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = []
    for server_name in MCP_SERVERS:
        async with mcp_session(server_name) as session:
            response = await session.list_tools()
            for tool in response.tools:
                raw = tool.model_dump(by_alias=True)
                tools.append({
                    "server": server_name,
                    "name": tool.name,
                    "public_name": f"{server_name}__{tool.name}",
                    "description": tool.description,
                    "input_schema": raw.get("inputSchema", {}),
                })
    return tools


async def discover_resources() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    for server_name in MCP_SERVERS:
        async with mcp_session(server_name) as session:
            response = await session.list_resources()
            resources.extend(
                {
                    "server": server_name,
                    "name": resource.name,
                    "uri": str(resource.uri),
                    "description": resource.description,
                }
                for resource in response.resources
            )
    return resources


async def server_statuses() -> list[dict[str, Any]]:
    """각 MCP 서버를 독립적으로 검사하여 부분 장애도 표시합니다."""
    statuses: list[dict[str, Any]] = []
    for server_name, config in MCP_SERVERS.items():
        try:
            async with mcp_session(server_name) as session:
                tool_count = len((await session.list_tools()).tools)
            statuses.append({
                "name": server_name,
                "status": "connected",
                "transport": config["transport"],
                "endpoint": config["url"],
                "tool_count": tool_count,
                "error": None,
            })
        except Exception as error:
            statuses.append({
                "name": server_name,
                "status": "disconnected",
                "transport": config["transport"],
                "endpoint": config["url"],
                "tool_count": 0,
                "error": str(error),
            })
    return statuses


async def read_resource(server_name: str, uri: str) -> str:
    async with mcp_session(server_name) as session:
        response = await session.read_resource(uri)
        return "\n".join(
            content.text for content in response.contents if hasattr(content, "text")
        )
