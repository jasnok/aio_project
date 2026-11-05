"""날씨 조회 입력 스키마."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeatherLocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    location: str = Field(min_length=1, max_length=50)

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        if not value:
            raise ValueError("location은 빈 문자열일 수 없습니다.")
        return value


class CurrentWeatherOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str
    observed_at: str
    sky_forecast_at: str
    temperature_c: str | float | None
    humidity_percent: str | float | None
    precipitation_1h_mm: str | float | None
    precipitation_type: str
    sky: str
    weather: str
    wind_speed_mps: str | float | None
    data_note: str
    source: Literal["기상청 단기예보 조회서비스"]


class NextWeekWeatherOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str
    message: str
    status: Literal["temporary"]
