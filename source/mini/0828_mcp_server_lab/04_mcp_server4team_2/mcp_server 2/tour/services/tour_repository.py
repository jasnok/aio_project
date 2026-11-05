from typing import Protocol


class TourRepository(Protocol):
    async def search(self, item_type: str, city: str, keyword=None, max_price=None, category=None, embedding=None) -> list[dict]: ...
