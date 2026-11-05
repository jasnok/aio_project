"""Weather 서비스 계약 테스트입니다."""

import unittest

from app.weather.schemas import WeatherLocationInput
from app.weather.services import weather_service


class WeatherServiceTests(unittest.TestCase):
    def test_next_week_weather_keeps_tool_contract(self):
        result = weather_service.next_week_weather(WeatherLocationInput(location="서울"))
        self.assertEqual(result["location"], "서울")
        self.assertEqual(result["status"], "temporary")


if __name__ == "__main__":
    unittest.main()
