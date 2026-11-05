import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class SearchPageTests(unittest.TestCase):
    def test_submitted_filter_survives_page_navigation_and_rerun(self):
        page = Path(__file__).resolve().parents[1]/'app_pages/03_listings.py'
        at = AppTest.from_file(str(page), default_timeout=15)
        at.session_state['loginout'] = 'logout'
        def response(page, size, search):
            return {'data': {'items': [{'id': 1, 'housing_name': '가상주택',
                'application_end_date': '2026-10-31'}], 'page': page,
                'total_pages': 2, 'total_count': 11}}
        with patch('clients.listing_client.get_listings_page', side_effect=response) as get:
            at.run()
            next(x for x in at.selectbox if x.label == '서울 자치구').select('강남구')
            next(x for x in at.number_input if x.label == '최대 보증금').set_value(10000000)
            next(x for x in at.button if x.label == '검색').click().run()
            self.assertEqual(get.call_args.args[2]['location'], '강남구')
            next(x for x in at.button if x.label == '다음').click().run()
            at.run()
            self.assertEqual(get.call_args.args[0], 2)
            self.assertEqual(get.call_args.args[2]['max_deposit'], 10000000)
            self.assertEqual(len(at.exception), 0)
