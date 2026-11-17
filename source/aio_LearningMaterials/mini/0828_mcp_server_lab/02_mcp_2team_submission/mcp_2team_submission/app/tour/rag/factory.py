from functools import lru_cache

from ..core.config import settings
from ..core.errors import ConfigurationError
from .protocols import EmbeddingProvider
from .providers.ollama_provider import OllamaEmbeddingProvider
from .providers.openai_provider import OpenAIEmbeddingProvider


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(
            model=settings.openai_embedding_model,
            dimensions=settings.openai_embedding_dimensions,
        )
    if settings.embedding_provider == "ollama":
        return OllamaEmbeddingProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            timeout=settings.ollama_request_timeout_seconds,
        )
    raise ConfigurationError(
        "TOUR_EMBEDDING_PROVIDER는 openai 또는 ollama여야 합니다."
    )
