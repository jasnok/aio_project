from openai import OpenAI

from ...core.errors import EmbeddingProviderError


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(self, *, model: str, dimensions: int):
        self.model = model
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise ValueError("임베딩할 텍스트는 비어 있을 수 없습니다.")
        response = OpenAI().embeddings.create(
            model=self.model, input=normalized, dimensions=self.dimensions
        )
        embedding = response.data[0].embedding
        if len(embedding) != self.dimensions:
            raise EmbeddingProviderError(
                f"OpenAI 임베딩 차원 불일치: expected={self.dimensions}, "
                f"actual={len(embedding)}"
            )
        return embedding
