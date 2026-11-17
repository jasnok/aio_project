import unittest
from unittest.mock import MagicMock, patch

from app.tour.schemas.policy import SearchHotelPoliciesInput
from app.tour.services import policy_service


POLICY_ROW = {
    "policy_id": 1,
    "hotel_id": "H1",
    "hotel_name": "테스트 호텔",
    "policy_type": "cancellation",
    "title": "취소 규정",
    "content": "당일 취소는 첫 1박 요금의 100%가 부과됩니다.",
    "effective_date": "2026-01-01",
    "similarity": 0.9,
    "is_mock": True,
}


class PolicyServiceTests(unittest.TestCase):
    @patch("app.tour.services.policy_service.policy_repository.search_similar")
    @patch("app.tour.services.policy_service.get_embedding_provider")
    def test_vector_policy_search_is_limited_to_hotel_ids(self, get_provider, search):
        provider = MagicMock(name="provider")
        provider.name = "ollama"
        provider.model = "embeddinggemma"
        provider.embed.return_value = [0.1, 0.2]
        get_provider.return_value = provider
        search.return_value = [POLICY_ROW]
        result = policy_service.search(SearchHotelPoliciesInput(
            hotel_ids=["H1"], question="당일 취소"
        ))
        self.assertEqual(result["search_mode"], "vector")
        self.assertEqual(result["items"][0]["hotel_id"], "H1")
        self.assertEqual(search.call_args.args[0], ["H1"])


if __name__ == "__main__":
    unittest.main()
