from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    city: str
    latitude: float
    longitude: float
    nx: int | None = None
    ny: int | None = None
