import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from .kma_provider import KmaProvider
from .open_meteo_client import OpenMeteoClient


class WeatherService:
    """공급자 선택과 공급자 간 비교만 담당하는 날씨 업무 서비스."""

    def __init__(self, providers=None, open_meteo=None, kma=None):
        self.providers = providers or {
            "open_meteo": open_meteo or OpenMeteoClient(),
            "kma": kma or KmaProvider(),
        }

    async def current(self, city: str, provider: str = "open_meteo") -> dict:
        return await self._provider(provider).current(city)

    async def forecast(self, city: str, days: int, provider: str = "open_meteo") -> dict:
        if days < 1 or days > 7:
            raise ValueError("days는 1 이상 7 이하여야 합니다.")
        return await self._provider(provider).forecast(city, days)

    async def compare_sources(self, city: str, days: int = 1) -> dict:
        async def fetch(name):
            try:
                return name, {"status": "ok", **await self.providers[name].forecast(city, days)}
            except Exception as exc:
                return name, {"status": "error", "message": str(exc), "retryable": True}

        pairs = await asyncio.gather(fetch("kma"), fetch("open_meteo"))
        results = dict(pairs)
        differences = []
        if results["kma"]["status"] == results["open_meteo"]["status"] == "ok":
            for kma, meteo in zip(results["kma"].get("forecast", []), results["open_meteo"].get("forecast", [])):
                kmax, mmax = kma.get("max_temperature_c"), meteo.get("max_temperature_c")
                differences.append({"date": kma.get("date"), "max_temperature_c":
                                    round(kmax - mmax, 2) if isinstance(kmax, (int, float)) and isinstance(mmax, (int, float)) else None})
        return {"requested_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
                "city": city, "kma": results["kma"], "open_meteo": results["open_meteo"],
                "differences": differences, "comparison_notes": ["두 공급자의 예보 모델이 다르므로 차이는 참고값입니다."]}

    def _provider(self, name):
        if name not in self.providers:
            raise ValueError(f"지원하지 않는 날씨 Provider입니다: {name}")
        return self.providers[name]
