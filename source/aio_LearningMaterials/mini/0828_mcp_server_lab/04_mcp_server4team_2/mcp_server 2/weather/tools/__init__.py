from .compare import register_compare_tool
from .current import register_current_tool
from .forecast import register_forecast_tool


def register_tools(mcp, service):
    register_current_tool(mcp, service)
    register_forecast_tool(mcp, service)
    register_compare_tool(mcp, service)
