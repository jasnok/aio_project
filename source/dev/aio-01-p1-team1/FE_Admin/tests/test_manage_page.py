import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class ManagePageTests(unittest.TestCase):
    def test_list_edit_cancel_and_image_delete_cancel(self):
        item = dict(id=1, title='가상공고', housing_name='가상주택', location='중구',
            area_sqm='26.5', recruitment_count=3, deposit=10000000, monthly_rent=280000,
            application_start_date='2026-10-01', application_end_date='2026-10-31',
            description='가상 설명', source_url='https://example.invalid/portfolio-demo/test',
            images=['https://example.invalid/image.png'] * 2, image_url='https://example.invalid/image.png')
        page=Path(__file__).resolve().parents[1]/'app_pages/03_listing_manage.py'
        at=AppTest.from_file(str(page), default_timeout=15)
        at.session_state['loginout']='login'
        at.session_state['admin_token']='unit-test-token'
        with patch('views.manage_list.get_listings_page', return_value={'data': {
            'items':[item], 'page':1, 'total_pages':1, 'total_count':1}}), \
             patch('views.manage_edit.get_listing', return_value={'data':item}), \
             patch('views.manage_images.replace_listing_images') as replace:
            at.run()
            next(b for b in at.button if b.label=='수정').click().run()
            self.assertEqual(len(at.exception),0)
            at.button(key='image-remove-1-0').click().run()
            self.assertEqual(len(at.exception),0)
            at.button(key='one-image-cancel').click().run()
            replace.assert_not_called()
            next(b for b in at.button if b.label=='취소').click().run()
            self.assertEqual(len(at.exception),0)
            self.assertTrue(any(b.label=='수정' for b in at.button))
