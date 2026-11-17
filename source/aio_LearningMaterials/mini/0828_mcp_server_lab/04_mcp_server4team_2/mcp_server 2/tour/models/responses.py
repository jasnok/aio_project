from typing import Any

from pydantic import BaseModel, Field


class TourSearchResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int
    source: str = "tour-vectors"
