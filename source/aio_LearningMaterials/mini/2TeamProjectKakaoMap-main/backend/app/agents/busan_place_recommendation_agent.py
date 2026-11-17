"""Agent that coordinates natural-language Busan place recommendations."""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.chat.intent_service import IntentService
from app.places.models import GuidePlace, PlaceCategory, SearchIntent
from app.tools.search_places import SearchPlacesTool


class PlaceRecommendationResult(BaseModel):
    """Structured result returned by the place recommendation agent."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer: str = Field(min_length=1)
    intent: SearchIntent
    places: list[GuidePlace] = Field(default_factory=list)
    warning: str = ""


class BusanPlaceRecommendationAgent:
    """Interpret a user request, search for places, and form a short answer."""

    def __init__(
        self,
        intent_service: IntentService,
        search_places_tool: SearchPlacesTool,
    ) -> None:
        self._intent_service = intent_service
        self._search_places_tool = search_places_tool

    async def run(
        self,
        message: str,
        recent_intents: Sequence[SearchIntent],
        *,
        district: str = "",
        category: PlaceCategory | None = None,
        quick_keyword: str = "",
    ) -> PlaceRecommendationResult:
        intent, intent_warning = self._intent_service.interpret(
            message,
            recent_intents,
            district=district,
            category=category,
            quick_keyword=quick_keyword,
        )
        search = await self._search_places_tool.run(intent)

        if search.places:
            names = ", ".join(place.name for place in search.places[:3])
            answer = (
                f"{search.intent.district or '부산'}에서 요청에 맞는 장소를 찾았어요. "
                f"먼저 {names}을(를) 살펴보세요."
            )
        else:
            answer = (
                "조건에 맞는 부산 장소를 찾지 못했어요. "
                "지역이나 키워드를 조금 바꿔 볼까요?"
            )

        warning = " ".join(
            item for item in (intent_warning, search.warning) if item
        )
        return PlaceRecommendationResult(
            answer=answer,
            intent=search.intent,
            places=search.places,
            warning=warning,
        )
