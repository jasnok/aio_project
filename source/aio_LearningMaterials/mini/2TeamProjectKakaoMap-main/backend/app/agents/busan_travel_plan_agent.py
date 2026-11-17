"""Agent that builds grounded, multi-place Busan travel itineraries."""

from app.places.models import GuidePlace, SearchIntent
from app.tools.get_favorite_places import GetFavoritePlacesTool
from app.tools.save_travel_plan import SaveTravelPlanTool
from app.tools.search_landmarks import SearchLandmarksTool
from app.tools.search_places import SearchPlacesTool
from app.travel.llm_service import TravelPlanLLMService
from app.travel.models import (
    BusanTravelPlanResult,
    ItineraryDraft,
    ScheduledTravelPlace,
    TravelCandidate,
    TravelPlanAgentRequest,
)


class BusanTravelPlanAgent:
    """Coordinate tools and limit the final itinerary to verified candidates."""

    def __init__(
        self,
        llm_service: TravelPlanLLMService,
        search_landmarks_tool: SearchLandmarksTool,
        search_places_tool: SearchPlacesTool,
        get_favorites_tool: GetFavoritePlacesTool | None = None,
        save_plan_tool: SaveTravelPlanTool | None = None,
    ) -> None:
        self._llm_service = llm_service
        self._search_landmarks_tool = search_landmarks_tool
        self._search_places_tool = search_places_tool
        self._get_favorites_tool = get_favorites_tool
        self._save_plan_tool = save_plan_tool

    async def run(self, request: TravelPlanAgentRequest) -> BusanTravelPlanResult:
        warnings: list[str] = []
        try:
            intent = self._llm_service.interpret(request.message)
        except Exception:
            intent = self._llm_service.deterministic_intent(request.message)
            warnings.append("여행 요청 분석에 실패해 기본 규칙으로 해석했습니다.")

        if intent.follow_up_question:
            return BusanTravelPlanResult(
                title="부산 여행 일정",
                summary="여행 일정을 만들기 위한 정보가 더 필요합니다.",
                nights=intent.nights,
                days=intent.days,
                preferences=intent.preferences,
                warnings=warnings,
                follow_up_question=intent.follow_up_question,
            )

        candidates: list[TravelCandidate] = []
        if intent.include_favorites:
            if request.user_id is None or self._get_favorites_tool is None:
                warnings.append("즐겨찾기를 포함하려면 로그인이 필요합니다.")
            else:
                favorites = self._get_favorites_tool.run(request.user_id)
                candidates.extend(self._favorite_candidate(place) for place in favorites)

        if request.landmark_count:
            landmark_result = await self._search_landmarks_tool.run(
                intent.destination,
                intent.landmark_queries or ["대표 관광명소"],
                request.landmark_count,
            )
            candidates.extend(
                TravelCandidate(
                    candidate_id=item.id,
                    name=item.name,
                    place_type="landmark",
                    category_name=item.category_name,
                    category_group_code="AT4",
                    address=item.address,
                    road_address=item.road_address,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    phone=item.phone,
                    kakao_place_url=item.kakao_place_url,
                )
                for item in landmark_result.landmarks
            )
            warnings.extend(item.message for item in landmark_result.warnings)

        if request.food_count:
            food_result = await self._search_places_tool.run(
                SearchIntent(category="food", keyword=intent.food_keyword),
                limit=request.food_count,
            )
            candidates.extend(self._place_candidate(place, "food") for place in food_result.places)
            if food_result.warning:
                warnings.append(food_result.warning)

        candidates = self._deduplicate_candidates(candidates)
        try:
            draft = self._llm_service.compose(request.message, intent, candidates)
        except Exception:
            draft = self._llm_service.deterministic_draft(intent, candidates)
            warnings.append("일정 구성에 실패해 검색 정확도 순으로 배치했습니다.")

        scheduled, rejected = self._ground_selections(draft, candidates, intent.days)
        if rejected:
            warnings.append("검색 후보에 없거나 유효하지 않은 일정 장소를 제외했습니다.")
        if not scheduled and candidates:
            draft = self._llm_service.deterministic_draft(intent, candidates)
            scheduled, _ = self._ground_selections(draft, candidates, intent.days)
            warnings.append("유효한 LLM 선택이 없어 검색 후보를 기본 순서로 배치했습니다.")

        result = BusanTravelPlanResult(
            title=draft.title,
            summary=draft.summary,
            nights=intent.nights,
            days=intent.days,
            preferences=intent.preferences,
            landmarks=[place for place in scheduled if place.place_type == "landmark"][:10],
            foods=[place for place in scheduled if place.place_type == "food"][:10],
            warnings=list(dict.fromkeys(warnings)),
        )

        if request.save_requested:
            if request.user_id is None or self._save_plan_tool is None:
                result.warnings.append("여행 일정을 저장하려면 로그인이 필요합니다.")
            else:
                plan_id = self._save_plan_tool.run(request.user_id, result)
                result = result.model_copy(update={"saved_plan_id": plan_id})
        return result

    @staticmethod
    def _favorite_candidate(place: GuidePlace) -> TravelCandidate:
        place_type = "landmark" if place.category_group_code == "AT4" else "food"
        return BusanTravelPlanAgent._place_candidate(place, place_type, favorite=True)

    @staticmethod
    def _place_candidate(
        place: GuidePlace,
        place_type: str,
        *,
        favorite: bool = False,
    ) -> TravelCandidate:
        return TravelCandidate(
            candidate_id=place.kakao_place_id,
            internal_place_id=place.id,
            name=place.name,
            place_type=place_type,
            category_name=place.category_name,
            category_group_code=place.category_group_code,
            address=place.address,
            road_address=place.road_address,
            latitude=place.latitude,
            longitude=place.longitude,
            phone=place.phone,
            kakao_place_url=place.kakao_place_url,
            is_favorite=favorite or place.is_favorite,
        )

    @staticmethod
    def _deduplicate_candidates(
        candidates: list[TravelCandidate],
    ) -> list[TravelCandidate]:
        unique: dict[str, TravelCandidate] = {}
        for candidate in candidates:
            current = unique.get(candidate.candidate_id)
            if current is None or (candidate.is_favorite and not current.is_favorite):
                unique[candidate.candidate_id] = candidate
        return list(unique.values())

    @staticmethod
    def _ground_selections(
        draft: ItineraryDraft,
        candidates: list[TravelCandidate],
        days: int,
    ) -> tuple[list[ScheduledTravelPlace], int]:
        by_id = {item.candidate_id: item for item in candidates}
        scheduled: list[ScheduledTravelPlace] = []
        used: set[str] = set()
        rejected = 0
        for selection in draft.selections:
            candidate = by_id.get(selection.candidate_id)
            if (
                candidate is None
                or selection.candidate_id in used
                or selection.day > days
            ):
                rejected += 1
                continue
            used.add(selection.candidate_id)
            scheduled.append(
                ScheduledTravelPlace(
                    id=candidate.candidate_id,
                    internal_place_id=candidate.internal_place_id,
                    name=candidate.name,
                    place_type=candidate.place_type,
                    category_name=candidate.category_name,
                    category_group_code=candidate.category_group_code,
                    description=selection.reason,
                    address=candidate.address,
                    road_address=candidate.road_address,
                    latitude=candidate.latitude,
                    longitude=candidate.longitude,
                    phone=candidate.phone,
                    kakao_place_url=candidate.kakao_place_url,
                    day=selection.day,
                    order=selection.order,
                    is_favorite=candidate.is_favorite,
                )
            )
        return sorted(scheduled, key=lambda item: (item.day, item.order)), rejected
