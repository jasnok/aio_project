"""외부 API와 DB 없이 실행하는 Tour 입력·출력 검증 테스트입니다."""

import unittest

from pydantic import ValidationError

from app.tour.schemas import SearchHotelsInput, SearchHotelsOutput


class TourSchemaTests(unittest.TestCase):
    def test_hotel_input_normalizes_text(self):
        payload = SearchHotelsInput(region=" 부산 ", query=" 오션뷰 ")
        self.assertEqual(payload.region, "부산")
        self.assertEqual(payload.query, "오션뷰")

    def test_hotel_count_has_upper_bound(self):
        with self.assertRaises(ValidationError):
            SearchHotelsInput(region="부산", count=21)

    def test_hotel_output_rejects_unknown_fields(self):
        with self.assertRaises(ValidationError):
            SearchHotelsOutput.model_validate({
                "items": [],
                "count": 0,
                "requested_count": 5,
                "filters": {"region": "부산", "max_price": None, "query": None},
                "sort": "price_asc",
                "search_mode": "structured",
                "source": "local-pgvector",
                "unexpected": True,
            })


if __name__ == "__main__":
    unittest.main()
