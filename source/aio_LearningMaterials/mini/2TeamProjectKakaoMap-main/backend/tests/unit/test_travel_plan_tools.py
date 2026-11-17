from uuid import UUID

from app.places.models import GuidePlace
from app.tools.get_favorite_places import GetFavoritePlacesTool
from app.tools.save_travel_plan import SaveTravelPlanTool
from app.travel.models import BusanTravelPlanResult, ScheduledTravelPlace


def guide_place() -> GuidePlace:
    return GuidePlace(
        id=UUID(int=1), kakao_place_id="kakao-1", name="즐겨찾기 장소",
        category_group_code="AT4", latitude=35.1, longitude=129.1,
        kakao_place_url="https://place.map.kakao.com/kakao-1",
    )


def scheduled(internal_id=None) -> ScheduledTravelPlace:
    return ScheduledTravelPlace(
        id="kakao-1", internal_place_id=internal_id, name="관광명소",
        place_type="landmark", category_group_code="AT4",
        description="추천 이유", latitude=35.1, longitude=129.1,
        kakao_place_url="https://place.map.kakao.com/kakao-1", day=1, order=1,
    )


class FakeFavorites:
    def __init__(self): self.user_id = None
    def list(self, user_id): self.user_id = user_id; return [guide_place()]


class FakePlaces:
    def __init__(self): self.rows = []
    def upsert_places(self, rows):
        self.rows = rows
        return [{**row, "id": UUID(int=9)} for row in rows]


class FakePlans:
    def __init__(self): self.created = 0; self.links = []; self.deleted = []
    def create_plan(self, **kwargs): self.created += 1; return UUID(int=7)
    def add_places(self, plan_id, places): self.links = places
    def delete_plan(self, plan_id): self.deleted.append(plan_id)


def test_get_favorite_places_delegates_to_repository() -> None:
    repository = FakeFavorites()
    user_id = UUID(int=3)
    result = GetFavoritePlacesTool(repository).run(user_id)
    assert repository.user_id == user_id
    assert result[0].is_favorite is False


def test_save_plan_resolves_missing_internal_place_id_before_linking() -> None:
    plans, places = FakePlans(), FakePlaces()
    plan = BusanTravelPlanResult(
        title="부산 하루 일정", summary="요약", nights=0, days=1,
        landmarks=[scheduled()],
    )
    plan_id = SaveTravelPlanTool(plans, places).run(UUID(int=2), plan)
    assert plan_id == UUID(int=7)
    assert plans.created == 1
    assert places.rows[0]["kakao_place_id"] == "kakao-1"
    assert plans.links[0]["place_id"] == str(UUID(int=9))
    assert plans.links[0]["day_number"] == 1


def test_save_plan_reuses_existing_internal_place_id() -> None:
    plans, places = FakePlans(), FakePlaces()
    plan = BusanTravelPlanResult(
        title="부산 하루 일정", summary="요약", nights=0, days=1,
        landmarks=[scheduled(UUID(int=5))],
    )
    SaveTravelPlanTool(plans, places).run(UUID(int=2), plan)
    assert places.rows == []
    assert plans.links[0]["place_id"] == str(UUID(int=5))
