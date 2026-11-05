"""Weather 입력·출력 검증 테스트입니다."""

import unittest

from pydantic import ValidationError

from app.weather.schemas import NextWeekWeatherOutput, WeatherLocationInput


class WeatherSchemaTests(unittest.TestCase):
    def test_weather_location_must_not_be_blank(self):
        with self.assertRaises(ValidationError):
            WeatherLocationInput(location="   ")

    def test_weather_output_contract(self):
        output = NextWeekWeatherOutput.model_validate({
            "location": "서울",
            "message": "연결 성공",
            "status": "temporary",
        })
        self.assertEqual(output.status, "temporary")


if __name__ == "__main__":
    unittest.main()
