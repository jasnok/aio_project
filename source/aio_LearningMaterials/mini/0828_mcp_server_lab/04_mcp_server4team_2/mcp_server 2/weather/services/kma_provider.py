from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .coordinate_converter import resolve_location
from .kma_client import KmaClient
from .weather_mapper import map_kma_items, to_number


class KmaProvider:
    name = "kma"

    def __init__(self, client=None):
        self.client = client

    def _get_client(self):
        if self.client is None:
            self.client = KmaClient()
        return self.client

    async def current(self, city: str) -> dict:
        loc = await resolve_location(city)
        base = self._latest_observation_base(datetime.now(ZoneInfo("Asia/Seoul")))
        items = await self._get_client().get_ultra_short_observation(base.strftime("%Y%m%d"), base.strftime("%H%M"), loc.nx, loc.ny)
        values = {item.get("category"): to_number(item.get("obsrValue")) for item in items}
        return {"city": city, "condition": self._pty_label(values.get("PTY")), "temperature_c": values.get("T1H"),
                "humidity": values.get("REH"), "wind_speed_kmh": round(values["WSD"] * 3.6, 1) if values.get("WSD") is not None else None,
                "observed_at": base.isoformat(), "source": self.name, "base_date": base.strftime("%Y%m%d"), "base_time": base.strftime("%H%M")}

    async def forecast(self, city: str, days: int) -> dict:
        loc = await resolve_location(city)
        base = self._latest_village_base(datetime.now(ZoneInfo("Asia/Seoul")))
        items = await self._get_client().get_village_forecast(base.strftime("%Y%m%d"), base.strftime("%H%M"), loc.nx, loc.ny)
        mapped = map_kma_items(items)
        dates = sorted({date for date, _ in mapped})[:days]
        forecast = []
        for date in dates:
            rows = [values for (item_date, _), values in mapped.items() if item_date == date]
            temps = [to_number(row.get("TMP")) for row in rows if to_number(row.get("TMP")) is not None]
            pops = [to_number(row.get("POP")) for row in rows if to_number(row.get("POP")) is not None]
            forecast.append({"date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "condition": self._condition(rows),
                             "min_temperature_c": min(temps) if temps else None, "max_temperature_c": max(temps) if temps else None,
                             "precipitation_probability": max(pops) if pops else None})
        return {"city": city, "forecast": forecast, "source": self.name,
                "base_date": base.strftime("%Y%m%d"), "base_time": base.strftime("%H%M")}

    @staticmethod
    def _latest_observation_base(now):
        candidate = now.replace(minute=0, second=0, microsecond=0)
        return candidate if now.minute >= 10 else candidate - timedelta(hours=1)

    @staticmethod
    def _latest_village_base(now):
        candidate = now - timedelta(minutes=10)
        for hour in (23, 20, 17, 14, 11, 8, 5, 2):
            point = candidate.replace(hour=hour, minute=0, second=0, microsecond=0)
            if point <= candidate:
                return point
        return (candidate - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)

    @staticmethod
    def _pty_label(value):
        return {0: "맑음", 1: "비", 2: "비/눈", 3: "눈", 4: "소나기", 5: "빗방울", 6: "빗방울눈날림", 7: "눈날림"}.get(value, "알 수 없음")

    @classmethod
    def _condition(cls, rows):
        pty = next((to_number(row.get("PTY")) for row in rows if row.get("PTY") not in (None, "-")), 0)
        if pty:
            return cls._pty_label(pty)
        sky = next((to_number(row.get("SKY")) for row in rows if row.get("SKY") is not None), None)
        return {1: "맑음", 3: "구름많음", 4: "흐림"}.get(sky, "알 수 없음")
