import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from admin_test_auth import enable_admin_for_unit_tests
from test_listing_images import make_row, PHOTO_A, PHOTO_B
from app.schemas.listing_schema import ListingPublic


class ImageSaveFailureTests(unittest.TestCase):
    def test_db_exception_cleans_new_upload_and_preserves_old_file(self):
        enable_admin_for_unit_tests(app)
        client = TestClient(app, raise_server_exceptions=False)
        current = ListingPublic.model_validate(make_row(image_url=PHOTO_A, images=[PHOTO_A]))
        with patch('app.services.listing_mutations.listing_get', return_value=current), \
             patch('app.services.listing_mutations.upload_listing_images', return_value=[PHOTO_B]), \
             patch('app.services.listing_mutations.listing_update', side_effect=RuntimeError('DB failure')), \
             patch('app.services.listing_mutations.delete_listing_image') as cleanup:
            response = client.put('/admin/listings/1/images', data={'keep_count': 1, 'kept_image_urls': [PHOTO_A]})
        self.assertEqual(response.status_code, 500)
        cleanup.assert_called_once_with(PHOTO_B)
