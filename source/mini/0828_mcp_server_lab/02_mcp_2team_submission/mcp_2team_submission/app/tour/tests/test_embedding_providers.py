import unittest
from unittest.mock import MagicMock, patch

from app.tour.core.errors import EmbeddingProviderError
from app.tour.rag.providers.ollama_provider import OllamaEmbeddingProvider


class OllamaEmbeddingProviderTests(unittest.TestCase):
    @patch("app.tour.rag.providers.ollama_provider.httpx.post")
    def test_embed_uses_ollama_api(self, post):
        response = MagicMock()
        response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
        post.return_value = response
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434", model="embeddinggemma"
        )
        self.assertEqual(provider.embed("호텔 취소"), [0.1, 0.2, 0.3])
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["json"]["model"], "embeddinggemma")

    @patch("app.tour.rag.providers.ollama_provider.httpx.post")
    def test_invalid_response_is_rejected(self, post):
        response = MagicMock()
        response.json.return_value = {"embeddings": []}
        post.return_value = response
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434", model="embeddinggemma"
        )
        with self.assertRaises(EmbeddingProviderError):
            provider.embed("호텔 취소")


if __name__ == "__main__":
    unittest.main()
