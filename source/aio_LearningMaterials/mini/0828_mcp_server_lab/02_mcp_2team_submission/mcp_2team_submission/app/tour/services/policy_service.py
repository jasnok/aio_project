"""검색된 호텔 범위 안에서 정책 RAG를 수행합니다."""

from ..core.errors import EmbeddingProviderError
from ..rag import get_embedding_provider, vector_literal
from ..repositories import policy_repository
from ..schemas.policy import SearchHotelPoliciesInput


MOCK_NOTICE = (
    "프로젝트 검증을 위해 생성한 임의 정책입니다. 실제 예약 전 호텔 공식 규정을 확인하세요."
)


def search(request: SearchHotelPoliciesInput) -> dict:
    provider_name = None
    model_name = None
    try:
        provider = get_embedding_provider()
        embedding = provider.embed(request.question)
        provider_name = provider.name
        model_name = provider.model
        items = policy_repository.search_similar(
            request.hotel_ids,
            vector_literal(embedding),
            request.top_k_per_hotel,
            provider.name,
            provider.model,
            len(embedding),
        )
        if items:
            return {
                "question": request.question,
                "items": items,
                "count": len(items),
                "search_mode": "vector",
                "embedding_provider": provider_name,
                "embedding_model": model_name,
                "mock_data_notice": MOCK_NOTICE,
            }
    except EmbeddingProviderError:
        pass

    items = policy_repository.search_structured(
        request.hotel_ids, request.question, request.top_k_per_hotel
    )
    return {
        "question": request.question,
        "items": items,
        "count": len(items),
        "search_mode": "structured_fallback",
        "embedding_provider": provider_name,
        "embedding_model": model_name,
        "mock_data_notice": MOCK_NOTICE,
    }
