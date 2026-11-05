"""사용자 지역명을 TourAPI 지역코드로 변환합니다."""

from constants.regions import NATIONWIDE_ALIASES, REGION_ALIASES, REGIONS
from exceptions import AmbiguousLocationError
from repositories import TourApiRepository
from schemas.location import Region, ResolvedLocation


def _compact(value: str) -> str:
    return "".join(value.split())


def _district_key(value: str) -> str:
    compact = _compact(value)
    for suffix in ("특별자치시", "특별자치도", "광역시", "시", "군", "구"):
        if compact.endswith(suffix) and len(compact) > len(suffix):
            return compact[: -len(suffix)]
    return compact


class LocationService:
    def __init__(self, repository: TourApiRepository) -> None:
        self.repository = repository

    def _match_district(
        self,
        region: Region,
        district_text: str,
    ) -> ResolvedLocation | None:
        target = _district_key(district_text)
        for district in self.repository.get_districts(region.code):
            if _district_key(district.name) == target:
                return ResolvedLocation(
                    label=f"{region.name} {district.name}",
                    area_code=region.code,
                    sigungu_code=district.code,
                )
        return None

    def resolve(self, location: str) -> ResolvedLocation | None:
        compact = _compact(location)
        if not compact:
            raise ValueError("location은 빈 문자열일 수 없습니다.")
        if compact in NATIONWIDE_ALIASES:
            return ResolvedLocation("대한민국 전국", None)

        direct_region_code = REGION_ALIASES.get(compact)
        if direct_region_code:
            region = next(item for item in REGIONS if item.code == direct_region_code)
            return ResolvedLocation(region.name, region.code)

        for alias in sorted(REGION_ALIASES, key=len, reverse=True):
            if compact.startswith(alias) and compact != alias:
                region_code = REGION_ALIASES[alias]
                region = next(item for item in REGIONS if item.code == region_code)
                return self._match_district(region, compact[len(alias):])

        matches: list[ResolvedLocation] = []
        for region in REGIONS:
            match = self._match_district(region, compact)
            if match:
                matches.append(match)

        if len(matches) > 1:
            labels = ", ".join(match.label for match in matches)
            raise AmbiguousLocationError(
                f"'{location}'과 같은 이름의 지역이 여러 곳입니다: {labels}. "
                "시도명을 함께 입력해 주세요."
            )
        return matches[0] if matches else None
