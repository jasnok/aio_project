from uuid import UUID

from app.agents.busan_place_recommendation_agent import (
    BusanPlaceRecommendationAgent,
)
from app.chat.models import ChatMessage, ChatMessageRequest, ChatResponse, ChatThread
from app.chat.repository import SupabaseChatRepository


class ChatService:
    def __init__(
        self,
        repository: SupabaseChatRepository,
        recommendation_agent: BusanPlaceRecommendationAgent,
    ) -> None:
        self.repository = repository
        self.recommendation_agent = recommendation_agent

    def create_thread(self, user_id: UUID) -> ChatThread:
        return self.repository.create_thread(user_id)

    def list_threads(self, user_id: UUID) -> list[ChatThread]:
        return self.repository.list_threads(user_id)

    def list_messages(self, user_id: UUID, thread_id: UUID) -> list[ChatMessage]:
        return self.repository.list_messages(user_id, thread_id)

    async def ask(self, user_id: UUID, thread_id: UUID, request: ChatMessageRequest) -> ChatResponse:
        previous = self.repository.list_messages(user_id, thread_id)
        recent_intents = [item.structured_intent for item in previous if item.structured_intent]
        user_message = self.repository.add_message(thread_id, "user", request.message)
        recommendation = await self.recommendation_agent.run(
            request.message,
            recent_intents,
            district=request.district,
            category=request.category,
            quick_keyword=request.quick_keyword,
        )
        self.repository.add_message(
            thread_id,
            "assistant",
            recommendation.answer,
            recommendation.intent,
        )
        self.repository.record_search(
            user_message.id,
            recommendation.intent,
            recommendation.places,
        )
        return ChatResponse(
            thread_id=thread_id,
            answer=recommendation.answer,
            intent=recommendation.intent,
            places=recommendation.places,
            warning=recommendation.warning,
        )
