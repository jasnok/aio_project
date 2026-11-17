import httpx

from .. import config
from .coordinate_converter import resolve_location


def weather_label(code: int) -> str:
    if code == 0:
        return "맑음"
    if code in (1, 2, 3):
        return "구름"
    if code in (45, 48):
        return "안개"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "비"
    if code in (71, 73, 75, 77, 85, 86):
        return "눈"
    if code in (95, 96, 99):
        return "뇌우"
    return "알 수 없음"


class OpenMeteoClient:
    name = "open-meteo"

    async def current(self, city: str) -> dict:
        loc = await resolve_location(city)
        async with httpx.AsyncClient(timeout=config.TIMEOUT_SECONDS) as client:
            response = await client.get(f"{config.OPEN_METEO_BASE_URL}/v1/forecast", params={
                "latitude": loc.latitude, "longitude": loc.longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "timezone": "Asia/Seoul",
            })
            response.raise_for_status()
            current = response.json()["current"]
        return {"city": city, "condition": weather_label(current["weather_code"]),
                "temperature_c": current["temperature_2m"], "humidity": current["relative_humidity_2m"],
                "wind_speed_kmh": current["wind_speed_10m"], "observed_at": current["time"], "source": self.name}

    async def forecast(self, city: str, days: int) -> dict:
        loc = await resolve_location(city)
        async with httpx.AsyncClient(timeout=config.TIMEOUT_SECONDS) as client:
            response = await client.get(f"{config.OPEN_METEO_BASE_URL}/v1/forecast", params={
                "latitude": loc.latitude, "longitude": loc.longitude,
                "daily": "weather_code,temperature_2m_min,temperature_2m_max,precipitation_probability_max",
                "forecast_days": days, "timezone": "Asia/Seoul",
            })
            response.raise_for_status()
            daily = response.json()["daily"]
        return {"city": city, "forecast": [{
            "date": daily["time"][i], "condition": weather_label(daily["weather_code"][i]),
            "min_temperature_c": daily["temperature_2m_min"][i], "max_temperature_c": daily["temperature_2m_max"][i],
            "precipitation_probability": daily["precipitation_probability_max"][i],
        } for i in range(days)], "source": self.name}
