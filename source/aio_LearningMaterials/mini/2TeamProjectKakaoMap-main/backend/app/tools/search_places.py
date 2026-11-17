"""Agent-facing adapter for the existing place search service."""

from app.places.models import SearchIntent, SearchRequest, SearchResponse
from app.places.service import PlaceSearchService


class SearchPlacesTool:
    """Convert a structured intent into an existing place search request."""

    def __init__(self, service: PlaceSearchService) -> None:
        self._service = service

    async def run(
        self,
        intent: SearchIntent,
        *,
        limit: int = 10,
    ) -> SearchResponse:
        request = SearchRequest(
            district=intent.district,
            category=intent.category,
            keyword=intent.keyword,
            limit=limit,
        )
        return await self._service.search(request)
