from .. import config
from ..models.requests import WeatherRequest


def register_forecast_tool(mcp, service):
    @mcp.tool()
    async def get_weather_forecast(city: str, days: int = 3) -> dict:
        """도시의 일자별 예보 날씨를 조회합니다."""
        request = WeatherRequest(city=city, days=days)
        return await service.forecast(request.city, request.days, config.WEATHER_PROVIDER)

    return get_weather_forecast
