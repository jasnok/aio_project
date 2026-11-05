"""날씨 MCP Tool 진입 함수."""

from ..schemas import CurrentWeatherOutput, NextWeekWeatherOutput, WeatherLocationInput
from ..services import weather_service


def get_current_weather(location: str) -> dict:
    """지역의 현재 날씨를 조회합니다."""
    result = weather_service.current_weather(WeatherLocationInput(location=location))
    return CurrentWeatherOutput.model_validate(result).model_dump(mode="json")


def get_next_week_weather(location: str) -> dict:
    """지역의 4일 후부터 10일 후까지 중기예보를 조회합니다."""
    result = weather_service.next_week_weather(WeatherLocationInput(location=location))
    return NextWeekWeatherOutput.model_validate(result).model_dump(mode="json")
