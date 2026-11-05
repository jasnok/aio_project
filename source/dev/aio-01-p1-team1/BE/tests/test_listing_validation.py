import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from admin_test_auth import enable_admin_for_unit_tests
from test_listing_update import form_data, make_listing, TEST_PNG, UPDATE_PATH

enable_admin_for_unit_tests(app)

class ListingValidationTests(unittest.TestCase):
    def test_invalid_period_blocks_upload_and_db_write(self):
        data = form_data()
        data['application_end_date'] = '2026-07-01'
        with patch('app.services.listing_mutations.listing_get', return_value=make_listing()), \
             patch('app.services.listing_mutations.upload_listing_image') as upload, \
             patch('app.services.listing_mutations.listing_update') as save:
            response = TestClient(app).put(UPDATE_PATH, data=data,
                files={'image': ('new.png', TEST_PNG, 'image/png')})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['errors'][0]['field'], 'application_end_date')
        upload.assert_not_called()
        save.assert_not_called()

    def test_json_create_rejects_invalid_period_without_echoing_input(self):
        data = form_data('private-submitted-value')
        data['application_end_date'] = '2026-07-01'
        with patch('app.routers.admin_router.listing_create') as save:
            response = TestClient(app).post('/admin/listings/create', json=data)
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('private-submitted-value', response.text)
        save.assert_not_called()
