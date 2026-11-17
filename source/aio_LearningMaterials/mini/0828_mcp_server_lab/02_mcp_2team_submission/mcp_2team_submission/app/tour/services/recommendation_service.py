"""관광지 주변 호텔 추천 서비스."""

from ..rag import get_embedding_provider, vector_literal
from ..repositories import attraction_repository, hotel_repository
from ..schemas.attraction import RecommendHotelsInput


def recommend(request: RecommendHotelsInput) -> dict:
    attractions = attraction_repository.find_by_name(request.attraction_name)
    if not attractions:
        return {
            "status": "not_found", "attraction": None, "hotels": [], "count": 0,
            "message": "해당 관광지를 찾을 수 없습니다.", "source": "local-pgvector",
        }
    if len(attractions) > 1:
        return {
            "status": "ambiguous_attraction", "candidates": attractions,
            "message": "관광지 이름이 여러 건과 일치합니다. 정확한 이름을 입력해 주세요.",
            "source": "local-pgvector",
        }
    attraction = attractions[0]
    query_vector = None
    embedding_identity = None
    if request.query:
        provider = get_embedding_provider()
        embedding = provider.embed(request.query)
        query_vector = vector_literal(embedding)
        embedding_identity = (provider.name, provider.model, len(embedding))
    hotels = hotel_repository.find_near_attraction(
        attraction["city"], attraction["area"], request.max_price,
        request.count, query_vector, embedding_identity,
    )
    return {
        "status": "ok", "attraction": attraction, "hotels": hotels,
        "count": len(hotels), "requested_count": request.count,
        "filters": {"max_price": request.max_price, "query": request.query or None},
        "matching_basis": "same_area_then_same_city",
        "search_mode": "vector" if request.query else "structured",
        "distance_notice": "현재 추천은 행정구역 기준이며 실제 거리 계산 결과가 아닙니다.",
        "source": "local-pgvector",
    }
