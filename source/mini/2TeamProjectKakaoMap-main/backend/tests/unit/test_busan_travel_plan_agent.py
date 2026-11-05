import asyncio
from uuid import UUID

from app.agents.busan_travel_plan_agent import BusanTravelPlanAgent
from app.landmark_schemas import LandmarkCandidate, LandmarkSearchResult
from app.places.models import GuidePlace, SearchIntent, SearchResponse
from app.travel.models import (
    ItineraryDraft, ItinerarySelection, TravelPlanAgentRequest, TravelPlanIntent,
)


class FakeLLM:
    def __init__(self, *, include_favorites=False, malicious=False):
        self.include_favorites = include_favorites
        self.malicious = malicious
    def interpret(self, message):
        return TravelPlanIntent(
            nights=1, days=2, preferences=["바다", "맛집"],
            landmark_queries=["바다 관광명소"], food_keyword="맛집",
            include_favorites=self.include_favorites,
        )
    def compose(self, message, intent, candidates):
        selections = [
            ItinerarySelection(
                candidate_id=item.candidate_id, day=index % 2 + 1,
                order=1, reason=f"{item.name} 추천",
            )
            for index, item in enumerate(candidates)
        ]
        if self.malicious:
            selections.append(ItinerarySelection(
                candidate_id="invented-place", day=1, order=9, reason="가짜 장소",
            ))
        return ItineraryDraft(title="부산 2일 일정", summary="검증된 장소 일정", selections=selections)
    deterministic_intent = staticmethod(lambda message: TravelPlanIntent(nights=1, days=2, landmark_queries=["명소"]))
    deterministic_draft = staticmethod(lambda intent, candidates: ItineraryDraft(title="기본 일정", summary="기본 요약"))


class FakeLandmarks:
    async def run(self, destination, queries, limit):
        return LandmarkSearchResult(landmarks=[LandmarkCandidate(
            id="landmark-1", name="해운대해수욕장", category_name="관광명소",
            address="부산", road_address="부산 해운대구", latitude=35.1,
            longitude=129.1, phone="", kakao_place_url="https://place.map.kakao.com/landmark-1",
        )][:limit])


class FakePlaces:
    async def run(self, intent, *, limit=10):
        place = GuidePlace(
            id=UUID(int=10), kakao_place_id="food-1", name="부산 맛집",
            category_group_code="FD6", latitude=35.2, longitude=129.2,
            kakao_place_url="https://place.map.kakao.com/food-1",
        )
        return SearchResponse(intent=SearchIntent(category="food", keyword=intent.keyword), places=[place][:limit])


class FakeFavorites:
    def __init__(self): self.calls = 0
    def run(self, user_id):
        self.calls += 1
        return [GuidePlace(
            id=UUID(int=11), kakao_place_id="favorite-1", name="저장한 명소",
            category_group_code="AT4", latitude=35.3, longitude=129.3,
            kakao_place_url="https://place.map.kakao.com/favorite-1", is_favorite=True,
        )]


class FakeSave:
    def __init__(self): self.calls = 0
    def run(self, user_id, plan): self.calls += 1; return UUID(int=20)


def make_agent(*, favorites=None, save=None, malicious=False):
    return BusanTravelPlanAgent(
        FakeLLM(include_favorites=favorites is not None, malicious=malicious),
        FakeLandmarks(), FakePlaces(), favorites, save,
    )


def test_agent_builds_landmark_and_food_itinerary() -> None:
    result = asyncio.run(make_agent().run(TravelPlanAgentRequest(
        message="바다와 맛집 중심 2일 코스", landmark_count=1, food_count=1,
    )))
    assert [item.id for item in result.landmarks] == ["landmark-1"]
    assert [item.id for item in result.foods] == ["food-1"]
    assert {item.day for item in [*result.landmarks, *result.foods]} == {1, 2}


def test_agent_includes_favorites_only_when_requested_by_intent() -> None:
    favorites = FakeFavorites()
    result = asyncio.run(make_agent(favorites=favorites).run(TravelPlanAgentRequest(
        message="즐겨찾기를 포함한 부산 2일 코스", user_id=UUID(int=1),
        landmark_count=0, food_count=0,
    )))
    assert favorites.calls == 1
    assert result.landmarks[0].id == "favorite-1"
    assert result.landmarks[0].is_favorite is True


def test_agent_does_not_save_without_explicit_request() -> None:
    save = FakeSave()
    asyncio.run(make_agent(save=save).run(TravelPlanAgentRequest(
        message="부산 2일 코스", user_id=UUID(int=1), save_requested=False,
    )))
    assert save.calls == 0


def test_agent_saves_only_with_explicit_request() -> None:
    save = FakeSave()
    result = asyncio.run(make_agent(save=save).run(TravelPlanAgentRequest(
        message="부산 2일 코스를 저장해줘", user_id=UUID(int=1), save_requested=True,
    )))
    assert save.calls == 1
    assert result.saved_plan_id == UUID(int=20)


def test_agent_rejects_llm_places_outside_search_candidates() -> None:
    result = asyncio.run(make_agent(malicious=True).run(TravelPlanAgentRequest(
        message="부산 2일 코스", landmark_count=1, food_count=1,
    )))
    assert "invented-place" not in {item.id for item in [*result.landmarks, *result.foods]}
    assert any("후보" in warning for warning in result.warnings)
