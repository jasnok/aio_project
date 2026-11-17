"""관광지 검색 순서와 결과 생성을 담당합니다."""

from mappers import map_tour_spots
from repositories import TourApiRepository
from schemas.tour_spot import TourSpotSearchResult
from services.location_service import LocationService


class TourSpotService:
    def __init__(
        self,
        repository: TourApiRepository,
        location_service: LocationService,
    ) -> None:
        self.repository = repository
        self.location_service = location_service

    def search(self, location: str, limit: int = 5) -> TourSpotSearchResult:
        normalized_location = location.strip()
        if not normalized_location:
            raise ValueError("location은 빈 문자열일 수 없습니다.")
        if not 1 <= limit <= 10:
            raise ValueError("limit은 1~10 범위여야 합니다.")

        resolved = self.location_service.resolve(normalized_location)
        if resolved is None:
            return TourSpotSearchResult(
                location=normalized_location,
                count=0,
                items=[],
                message=(
                    "국내 지역코드에서 찾을 수 없습니다. 대한민국 국내 지역명을 "
                    "확인해 주세요. 해외 관광지는 지원하지 않습니다."
                ),
            )

        body = self.repository.search_attractions(resolved, limit)
        spots = map_tour_spots(body)
        return TourSpotSearchResult(
            location=normalized_location,
            resolved_location=resolved.label,
            count=len(spots),
            items=spots,
            message=None if spots else "해당 지역에서 관광지 검색 결과를 찾지 못했습니다.",
        )
