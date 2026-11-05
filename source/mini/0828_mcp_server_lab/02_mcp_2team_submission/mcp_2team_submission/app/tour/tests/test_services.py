"""외부 연결을 대체하여 Tour 서비스 흐름을 확인합니다."""

import unittest
from unittest.mock import patch

from app.tour.schemas import SearchHotelsInput
from app.tour.services import hotel_service


class TourServiceTests(unittest.TestCase):
    @patch("app.tour.services.hotel_service.hotel_repository.search_structured")
    def test_structured_hotel_search(self, search_structured):
        search_structured.return_value = [{"hotel_id": "H1", "name": "테스트 호텔"}]
        result = hotel_service.search(SearchHotelsInput(region="부산"))
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["search_mode"], "structured")
        search_structured.assert_called_once_with("부산", None, 5)


if __name__ == "__main__":
    unittest.main()
