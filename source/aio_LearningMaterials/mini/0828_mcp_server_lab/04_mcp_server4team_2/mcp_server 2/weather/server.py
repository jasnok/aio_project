from mcp.server.fastmcp import FastMCP

from . import config
from .prompts import register_prompts
from .resources import register_resources
from .services import WeatherService
from .tools import register_tools


mcp = FastMCP("mini-agent-weather", instructions="현재 날씨와 예보 날씨를 제공하는 서버입니다.",
              host=config.MCP_HOST, port=config.MCP_PORT, stateless_http=True, json_response=True)
service = WeatherService()
register_tools(mcp, service)
register_resources(mcp, service)
register_prompts(mcp)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
