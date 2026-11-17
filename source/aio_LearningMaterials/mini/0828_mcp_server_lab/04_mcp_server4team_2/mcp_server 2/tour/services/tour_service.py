from .result_formatter import format_results
from .tour_db import PostgresTourRepository
from .tour_rag import EmbeddingService


class TourService:
    def __init__(self, repository=None, embeddings=None):
        self.repository = repository or PostgresTourRepository()
        self.embeddings = embeddings or EmbeddingService()

    async def search_hotels(self, city, max_price=None, keyword=None):
        vector = await self.embeddings.embed(keyword) if keyword else None
        rows = await self.repository.search("hotel", city, keyword, max_price=max_price, embedding=vector)
        return format_results(rows)

    async def search_spots(self, city, category=None, keyword=None):
        vector = await self.embeddings.embed(keyword) if keyword else None
        rows = await self.repository.search("spot", city, keyword, category=category, embedding=vector)
        return format_results(rows)
