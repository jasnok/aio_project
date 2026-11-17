import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class EmbeddingService:
    async def embed(self, text: str) -> list[float]:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma")
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{base_url}/api/embed", json={"model": model, "input": text})
            response.raise_for_status()
            embeddings = response.json().get("embeddings", [])
        if not embeddings or len(embeddings[0]) != 768:
            raise ValueError("Tour embedding은 768차원이어야 합니다.")
        return embeddings[0]
