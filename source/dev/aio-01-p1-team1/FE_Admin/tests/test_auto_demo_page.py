"""가상 결과의 검토·수정·등록 여정을 실제 Streamlit 페이지로 검사합니다."""
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class AutoDemoPageTests(unittest.TestCase):
    def test_missing_value_blocks_save_and_correction_enables_save(self):
        page = Path(__file__).resolve().parents[1] / 'app_pages/08_listing_auto_create.py'
        at = AppTest.from_file(str(page), default_timeout=15)
        at.session_state['loginout'] = 'login'
        at.session_state['admin_token'] = 'unit-test-token'
        with patch('clients.gemini_client.extract_listings_from_pdf') as ai, \
             patch('clients.listing_client.create_listing', return_value={'success': True}) as create:
            at.run()
            next(b for b in at.button if b.label == '가상 분석 결과 불러오기').click().run()
            self.assertTrue(next(b for b in at.button if b.label == '선택한 0건 등록').disabled)
            next(n for n in at.number_input if n.label == '월세').set_value(280000)
            next(b for b in at.button if b.label == '이 값으로 다시 확인').click().run()
            next(b for b in at.button if b.label == '선택한 1건 등록').click().run()
            self.assertEqual(len(at.exception), 0)
            create.assert_called_once()
            self.assertEqual(create.call_args.args[0]['monthly_rent'], 280000)
            ai.assert_not_called()
            at.run()
            self.assertFalse(any(b.label.startswith('선택한') for b in at.button))

    def test_partial_retry_does_not_repeat_successful_items(self):
        from core.auto_demo import sample_analysis
        from core.api_client import BackendAPIError
        first = sample_analysis()[0]
        first['monthly_rent'] = 280000
        second = dict(first, housing_name='두 번째 가상 주택')
        page = Path(__file__).resolve().parents[1] / 'app_pages/08_listing_auto_create.py'
        at = AppTest.from_file(str(page), default_timeout=15)
        at.session_state['loginout'] = 'login'
        at.session_state['admin_token'] = 'unit-test-token'
        with patch('core.auto_demo.sample_analysis', return_value=[first, second]), \
             patch('clients.listing_client.create_listing', side_effect=[
                 {'success': True}, BackendAPIError('잠시 실패'), {'success': True}
             ]) as create:
            at.run()
            next(b for b in at.button if b.label == '가상 분석 결과 불러오기').click().run()
            next(b for b in at.button if b.label == '선택한 2건 등록').click().run()
            at.run()
            next(b for b in at.button if b.label == '선택한 1건 등록').click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertEqual([c.args[0]['housing_name'] for c in create.call_args_list],
                             [first['housing_name'], second['housing_name'], second['housing_name']])
