import httpx

from .. import config
from ..models.kma import response_items


class KmaClient:
    name = "kma"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or config.KMA_API_KEY
        if not self.api_key:
            raise ValueError("KMA_API_KEY가 설정되지 않았습니다.")

    async def _get(self, operation: str, params: dict) -> list[dict]:
        query = {"serviceKey": self.api_key, "numOfRows": 1000, "pageNo": 1, "dataType": "JSON", **params}
        async with httpx.AsyncClient(timeout=config.TIMEOUT_SECONDS) as client:
            response = await client.get(f"{config.KMA_BASE_URL}/{operation}", params=query)
            response.raise_for_status()
            return response_items(response.json())

    async def get_ultra_short_observation(self, base_date: str, base_time: str, nx: int, ny: int) -> list[dict]:
        return await self._get("getUltraSrtNcst", {"base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny})

    async def get_ultra_short_forecast(self, base_date: str, base_time: str, nx: int, ny: int) -> list[dict]:
        return await self._get("getUltraSrtFcst", {"base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny})

    async def get_village_forecast(self, base_date: str, base_time: str, nx: int, ny: int) -> list[dict]:
        return await self._get("getVilageFcst", {"base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny})

    async def get_forecast_version(self, ftype: str, basedatetime: str) -> list[dict]:
        return await self._get("getFcstVersion", {"ftype": ftype, "basedatetime": basedatetime})
