from .. import config
from ..models.requests import WeatherRequest


def register_current_tool(mcp, service):
    @mcp.tool()
    async def get_current_weather(city: str) -> dict:
        """도시의 현재 날씨를 조회합니다."""
        request = WeatherRequest(city=city, days=1)
        return await service.current(request.city, config.WEATHER_PROVIDER)

    return get_current_weather
