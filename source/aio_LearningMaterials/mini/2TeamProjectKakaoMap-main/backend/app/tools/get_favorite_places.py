"""Agent-facing adapter for the existing favorites repository."""

from uuid import UUID

from app.favorites.repository import SupabaseFavoriteRepository
from app.places.models import GuidePlace


class GetFavoritePlacesTool:
    def __init__(self, repository: SupabaseFavoriteRepository) -> None:
        self._repository = repository

    def run(self, user_id: UUID) -> list[GuidePlace]:
        return self._repository.list(user_id)
