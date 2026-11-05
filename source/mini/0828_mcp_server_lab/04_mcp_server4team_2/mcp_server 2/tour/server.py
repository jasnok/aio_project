from mcp.server.fastmcp import FastMCP

from .services import TourService
from .tools import register_tools
from .resources import register_resources
from .prompts import register_prompts


mcp = FastMCP("mini-agent-tour", instructions="호텔과 관광지 정보를 제공하는 서버입니다.", host="127.0.0.1", port=8020, stateless_http=True, json_response=True)
service = TourService()
register_tools(mcp, service)
register_resources(mcp, service)
register_prompts(mcp)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
