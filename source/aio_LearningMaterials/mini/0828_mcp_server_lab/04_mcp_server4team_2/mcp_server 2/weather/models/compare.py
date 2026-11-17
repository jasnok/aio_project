from typing import Any

from pydantic import BaseModel, Field


class ComparisonResult(BaseModel):
    location: dict[str, Any]
    requested_at: str
    kma: dict[str, Any]
    open_meteo: dict[str, Any]
    differences: list[dict[str, Any]] = Field(default_factory=list)
    comparison_notes: list[str] = Field(default_factory=list)
