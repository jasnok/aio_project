"""국내 지역코드 판별에 사용하는 데이터 형식입니다."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    code: str
    name: str


@dataclass(frozen=True)
class ResolvedLocation:
    label: str
    area_code: str | None
    sigungu_code: str | None = None
