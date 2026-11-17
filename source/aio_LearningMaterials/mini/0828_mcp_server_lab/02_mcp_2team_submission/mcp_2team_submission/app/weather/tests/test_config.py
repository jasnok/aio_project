"""Weather 환경설정과 KMA URL 검증 테스트입니다."""

import unittest
from dataclasses import replace

from app.weather.core.config import settings


class WeatherConfigTests(unittest.TestCase):
    def test_kma_version_is_explicit(self):
        self.assertTrue(settings.kma_api_version)
        settings.validate()

    def test_invalid_kma_url_is_rejected(self):
        invalid = replace(settings, kma_api_base_url="not-a-url")
        with self.assertRaises(ValueError):
            invalid.validate()


if __name__ == "__main__":
    unittest.main()
