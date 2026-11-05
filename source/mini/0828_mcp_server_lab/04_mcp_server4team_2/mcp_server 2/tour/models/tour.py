from dataclasses import dataclass


@dataclass(frozen=True)
class TourItem:
    id: str
    content: str
    metadata: dict
