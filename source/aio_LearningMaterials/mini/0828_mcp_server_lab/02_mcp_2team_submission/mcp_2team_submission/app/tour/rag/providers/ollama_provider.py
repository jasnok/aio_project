import httpx

from ...core.errors import EmbeddingProviderError


class OllamaEmbeddingProvider:
    name = "ollama"

    def __init__(self, *, base_url: str, model: str, timeout: float = 120):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed(self, text: str) -> list[float]:
        normalized = text.strip()
        if not normalized:
            raise ValueError("임베딩할 텍스트는 비어 있을 수 없습니다.")
        try:
            response = httpx.post(
                f"{self.base_url}/api/embed",
                json={"model": self.model, "input": normalized},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            embedding = payload["embeddings"][0]
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
            raise EmbeddingProviderError(
                f"Ollama 임베딩 호출 실패: model={self.model}, error={error}"
            ) from None
        if not embedding or not all(isinstance(value, (int, float)) for value in embedding):
            raise EmbeddingProviderError("Ollama가 유효한 임베딩 벡터를 반환하지 않았습니다.")
        return [float(value) for value in embedding]
