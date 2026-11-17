from typing import Protocol


class WeatherProvider(Protocol):
    name: str

    async def current(self, city: str) -> dict: ...

    async def forecast(self, city: str, days: int) -> dict: ...
