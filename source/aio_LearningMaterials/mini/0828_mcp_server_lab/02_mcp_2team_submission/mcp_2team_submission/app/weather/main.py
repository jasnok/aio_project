"""날씨 Streamable HTTP MCP 서버."""

from mcp.server.fastmcp import FastMCP

from .core.config import settings
from .tools.weather_tools import get_current_weather, get_next_week_weather


mcp = FastMCP(
    "weather-mcp",
    instructions="기상청 날씨 정보를 제공하는 학습용 MCP Server입니다.",
    host=settings.mcp_host,
    port=settings.mcp_port,
    stateless_http=True,
    json_response=True,
)
mcp.tool()(get_current_weather)
mcp.tool()(get_next_week_weather)


def main() -> None:
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
