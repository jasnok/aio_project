from dataclasses import dataclass


@dataclass(frozen=True)
class SearchFilters:
    item_type: str
    city: str
    keyword: str | None = None
    max_price: int | None = None
    category: str | None = None
