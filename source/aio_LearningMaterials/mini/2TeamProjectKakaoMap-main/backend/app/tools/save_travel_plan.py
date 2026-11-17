"""Persist a generated travel plan only after an explicit save request."""

from uuid import UUID

from app.places.repository import PlaceRepository
from app.travel.models import BusanTravelPlanResult, ScheduledTravelPlace
from app.travel.repository import TravelPlanRepository


class SaveTravelPlanTool:
    def __init__(
        self,
        travel_repository: TravelPlanRepository,
        place_repository: PlaceRepository,
    ) -> None:
        self._travel_repository = travel_repository
        self._place_repository = place_repository

    def run(self, user_id: UUID, plan: BusanTravelPlanResult) -> UUID:
        places = [*plan.landmarks, *plan.foods]
        place_ids = self._resolve_place_ids(places)
        plan_id = self._travel_repository.create_plan(
            user_id=user_id,
            title=plan.title,
            summary=plan.summary,
            days=plan.days,
        )
        try:
            self._travel_repository.add_places(
                plan_id,
                [
                    {
                        "place_id": str(place_ids[place.id]),
                        "day_number": place.day,
                        "display_order": place.order,
                        "note": place.description,
                    }
                    for place in places
                ],
            )
        except Exception:
            self._travel_repository.delete_plan(plan_id)
            raise
        return plan_id

    def _resolve_place_ids(
        self,
        places: list[ScheduledTravelPlace],
    ) -> dict[str, UUID]:
        resolved = {
            place.id: place.internal_place_id
            for place in places
            if place.internal_place_id is not None
        }
        unresolved = [place for place in places if place.internal_place_id is None]
        if unresolved:
            rows = self._place_repository.upsert_places(
                [self._place_row(place) for place in unresolved]
            )
            resolved.update(
                {str(row["kakao_place_id"]): UUID(str(row["id"])) for row in rows}
            )
        missing = [place.id for place in places if place.id not in resolved]
        if missing:
            raise RuntimeError("일정 장소의 내부 place_id를 확인할 수 없습니다.")
        return resolved

    @staticmethod
    def _place_row(place: ScheduledTravelPlace) -> dict:
        return {
            "kakao_place_id": place.id,
            "name": place.name,
            "category_name": place.category_name,
            "category_group_code": place.category_group_code,
            "address": place.address,
            "road_address": place.road_address,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "phone": place.phone,
            "kakao_place_url": place.kakao_place_url,
            "raw_snapshot": {},
        }
