from typing import Any

from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    city: str
    condition: str
    temperature_c: float | int | None = None
    humidity: float | int | None = None
    wind_speed_kmh: float | int | None = None
    observed_at: str | None = None
    source: str


class ForecastResponse(BaseModel):
    city: str
    forecast: list[dict[str, Any]] = Field(default_factory=list)
    source: str
