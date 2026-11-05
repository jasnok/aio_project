import json
import re
from collections.abc import Sequence

import httpx

from app.config import settings
from app.travel.models import (
    ItineraryDraft,
    ItinerarySelection,
    ProviderName,
    TravelCandidate,
    TravelPlanIntent,
)


class TravelPlanLLMService:
    """Produce structured intent and candidate-ID-only itinerary decisions."""

    def __init__(self, provider: ProviderName) -> None:
        self.provider = provider

    def interpret(self, message: str) -> TravelPlanIntent:
        if self.provider == "mock":
            return self.deterministic_intent(message)
        prompt = (
            "부산 여행 일정 요청을 구조화하세요. destination은 부산입니다. "
            "days는 nights보다 정확히 1 커야 합니다. 관광명소 검색어는 최대 5개이며 "
            "즐겨찾기 포함 요청 여부도 판단하세요.\n사용자 요청: " + message
        )
        return self._generate(prompt, TravelPlanIntent)

    def compose(
        self,
        message: str,
        intent: TravelPlanIntent,
        candidates: Sequence[TravelCandidate],
    ) -> ItineraryDraft:
        if self.provider == "mock":
            return self.deterministic_draft(intent, candidates)
        candidate_payload = [
            {
                "candidate_id": item.candidate_id,
                "name": item.name,
                "place_type": item.place_type,
                "category_name": item.category_name,
                "address": item.road_address or item.address,
                "is_favorite": item.is_favorite,
            }
            for item in candidates
        ]
        prompt = (
            "사용자의 부산 여행 일정을 구성하세요. 반드시 제공된 candidate_id만 선택하세요. "
            "후보에 없는 장소나 ID를 만들지 마세요. 각 장소에 day, order, 추천 이유를 "
            "작성하세요.\n"
            f"사용자 요청: {message}\n여행 기간: {intent.days}일\n"
            f"후보: {json.dumps(candidate_payload, ensure_ascii=False)}"
        )
        return self._generate(prompt, ItineraryDraft)

    def _generate(self, prompt: str, model_class):
        if self.provider == "gemini":
            if not settings.gemini_api_key or not settings.gemini_model:
                raise RuntimeError("Gemini is not configured")
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=model_class.model_json_schema(),
                    temperature=0.2,
                ),
            )
            return model_class.model_validate_json(response.text or "{}")
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise RuntimeError("OpenAI is not configured")
            from openai import OpenAI

            response = OpenAI(api_key=settings.openai_api_key).responses.parse(
                model=settings.openai_model,
                input=prompt,
                text_format=model_class,
            )
            if response.output_parsed is None:
                raise RuntimeError("OpenAI returned no structured result")
            return response.output_parsed
        if self.provider == "ollama":
            response = httpx.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "format": model_class.model_json_schema(),
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            return model_class.model_validate_json(response.json()["message"]["content"])
        raise ValueError(f"Unsupported provider: {self.provider}")

    @staticmethod
    def deterministic_intent(message: str) -> TravelPlanIntent:
        nights, days = 2, 3
        duration = re.search(r"(\d+)\s*박\s*(\d+)\s*일", message)
        days_only = re.search(r"(\d+)\s*일", message)
        if duration:
            nights, days = int(duration.group(1)), int(duration.group(2))
            if days != nights + 1:
                days = nights + 1
        elif days_only:
            days = max(1, min(30, int(days_only.group(1))))
            nights = days - 1
        elif "하루" in message or "당일" in message:
            nights, days = 0, 1

        preference_words = (
            "가족", "아이", "부모님", "바다", "해산물", "맛집", "카페",
            "야경", "쇼핑", "역사", "문화", "자연", "데이트",
        )
        preferences = [word for word in preference_words if word in message]
        landmark_queries = [
            f"{word} 관광명소"
            for word in preferences
            if word not in {"맛집", "카페", "해산물"}
        ][:4]
        if not landmark_queries:
            landmark_queries = ["대표 관광명소"]
        food_words = [word for word in preferences if word in {"가족", "해산물", "맛집"}]
        return TravelPlanIntent(
            nights=nights,
            days=days,
            preferences=preferences,
            landmark_queries=landmark_queries,
            food_keyword=" ".join(food_words) or "맛집",
            include_favorites=("즐겨찾기" in message or "저장한 장소" in message),
        )

    @staticmethod
    def deterministic_draft(
        intent: TravelPlanIntent,
        candidates: Sequence[TravelCandidate],
    ) -> ItineraryDraft:
        selections = []
        day_orders = {day: 0 for day in range(1, intent.days + 1)}
        for index, candidate in enumerate(candidates):
            day = index % intent.days + 1
            day_orders[day] += 1
            selections.append(
                ItinerarySelection(
                    candidate_id=candidate.candidate_id,
                    day=day,
                    order=day_orders[day],
                    reason=f"{candidate.name}은(는) 요청한 부산 여행 취향에 어울리는 장소입니다.",
                )
            )
        duration = "당일" if intent.days == 1 else f"{intent.nights}박 {intent.days}일"
        return ItineraryDraft(
            title=f"부산 {duration} 여행 일정",
            summary="실제 Kakao 장소 후보를 날짜별로 구성한 부산 여행 일정입니다.",
            selections=selections,
        )
