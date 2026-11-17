"""관광지 검색 서비스."""

from ..rag import get_embedding_provider, vector_literal
from ..repositories import attraction_repository
from ..schemas.attraction import SearchAttractionsInput


def search(request: SearchAttractionsInput) -> dict:
    if request.query:
        provider = get_embedding_provider()
        embedding = provider.embed(request.query)
        query_vector = vector_literal(embedding)
        items = attraction_repository.search_similar(
            request.region, query_vector, request.count,
            provider.name, provider.model, len(embedding),
        )
        if items:
            return {
                "items": items,
                "count": len(items),
                "requested_count": request.count,
                "filters": {
                    "region": request.region,
                    "query": request.query,
                },
                "search_mode": "vector",
                "source": "local-pgvector",
            }
    items = attraction_repository.search_structured(request.region, request.count)
    return {
        "items": items,
        "count": len(items),
        "requested_count": request.count,
        "filters": {"region": request.region, "query": request.query or None},
        "search_mode": "structured_fallback" if request.query else "structured",
        "source": "local-pgvector",
    }
