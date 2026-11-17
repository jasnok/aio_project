from ..models.requests import WeatherRequest


def register_compare_tool(mcp, service):
    @mcp.tool()
    async def compare_weather_sources(city: str, days: int = 1) -> dict:
        """동일한 도시의 기상청과 Open-Meteo 날씨를 비교합니다."""
        request = WeatherRequest(city=city, days=days)
        return await service.compare_sources(request.city, request.days)

    return compare_weather_sources
