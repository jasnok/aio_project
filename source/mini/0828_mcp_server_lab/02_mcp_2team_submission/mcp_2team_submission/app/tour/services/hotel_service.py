"""호텔 검색 서비스."""

from ..rag import get_embedding_provider, vector_literal
from ..repositories import hotel_repository
from ..schemas.hotel import SearchHotelsInput


def search(request: SearchHotelsInput) -> dict:
    if request.query:
        provider = get_embedding_provider()
        embedding = provider.embed(request.query)
        query_vector = vector_literal(embedding)
        items = hotel_repository.search_similar(
            request.region, request.max_price, query_vector, request.count,
            provider.name, provider.model, len(embedding),
        )
        if items:
            return {
                "items": items,
                "count": len(items),
                "requested_count": request.count,
                "filters": {
                    "region": request.region,
                    "max_price": request.max_price,
                    "query": request.query,
                },
                "sort": "similarity_desc_then_price_asc",
                "search_mode": "vector",
                "source": "local-pgvector",
            }
    items = hotel_repository.search_structured(
        request.region, request.max_price, request.count
    )
    return {
        "items": items,
        "count": len(items),
        "requested_count": request.count,
        "filters": {
            "region": request.region,
            "max_price": request.max_price,
            "query": request.query or None,
        },
        "sort": "price_asc",
        "search_mode": "structured_fallback" if request.query else "structured",
        "source": "local-pgvector",
    }
