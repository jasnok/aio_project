"""Agent-facing adapter for the existing landmark search service."""

from collections.abc import Sequence

from app.landmark_schemas import LandmarkSearchResult
from app.services.landmark_search_service import LandmarkSearchService


class SearchLandmarksTool:
    """Delegate landmark candidate searches to the existing service."""

    def __init__(self, service: LandmarkSearchService) -> None:
        self._service = service

    async def run(
        self,
        destination: str,
        queries: Sequence[str],
        limit: int,
    ) -> LandmarkSearchResult:
        return await self._service.search(
            destination=destination,
            queries=queries,
            limit=limit,
        )
