from .hotels import register_hotel_tools
from .spots import register_spot_tools


def register_tools(mcp, service):
    register_hotel_tools(mcp, service)
    register_spot_tools(mcp, service)
