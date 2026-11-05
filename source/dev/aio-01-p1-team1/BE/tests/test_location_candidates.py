import unittest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.listing_router import listing_router
from app.exceptions.handlers import register_exception_handlers


class LocationCandidateTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI(); app.include_router(listing_router); register_exception_handlers(app)
        self.client = TestClient(app)

    def test_query_length_and_page_size_are_bounded(self):
        for params in ({'query': 'x', 'page_size': 51}, {'query': 'x' * 256}, {'query': 'x', 'page': 0}):
            self.assertEqual(self.client.get('/listings/location-candidates', params=params).status_code, 422)
        self.assertEqual(self.client.get('/listings/location-candidates', params={'query': '   '}).status_code, 400)

    def test_empty_page_contract_is_returned_without_loading_all_listings(self):
        db = MagicMock()
        db.rpc.return_value.execute.return_value.data = {'items': [], 'page': 1, 'page_size': 20, 'total_count': 0, 'total_pages': 1}
        with patch('app.services.listing_service.get_supabase', return_value=db):
            response = self.client.get('/listings/location-candidates', params={'query': '없는공고'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['total_count'], 0)
        db.table.assert_not_called()
