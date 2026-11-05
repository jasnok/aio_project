import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from clients.chat_client import ChatAPIError


class RefactoredViewTests(unittest.TestCase):
    def setUp(self):
        self.history_patch = patch('views.chat.get_chat_history', return_value={'data': []})
        self.history_patch.start()
        self.addCleanup(self.history_patch.stop)

    def test_first_visit_restores_server_history_only_once(self):
        at = self.chat()
        at.session_state['ai_chat_history_attempted'] = False
        at.session_state['ai_chat_history_ready'] = False
        messages = [{'role': 'user', 'content': '복원할 질문'}, {'role': 'assistant', 'content': '복원할 답변'}]
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.get_chat_history', return_value={'data': messages}) as history:
            at.run(); at.run()
            self.assertEqual(at.session_state['ai_chat_messages'], messages)
            self.assertEqual(history.call_count, 1)
            self.assertFalse(at.chat_input[0].disabled)
            self.assertEqual(len(at.exception), 0)

    def test_initial_restore_failure_blocks_mutation_until_manual_recovery(self):
        at = self.chat()
        at.session_state['ai_chat_history_attempted'] = False
        at.session_state['ai_chat_history_ready'] = False
        messages = [{'role': 'user', 'content': '서버 질문'}, {'role': 'assistant', 'content': '서버 답변'}]
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.get_chat_history', side_effect=[ChatAPIError('저장소 연결 실패'), {'data': messages}]) as history:
            at.run(); at.run()
            self.assertEqual(history.call_count, 1)
            self.assertTrue(at.chat_input[0].disabled)
            self.assertTrue(next(x for x in at.button if x.label == '대화 저장').disabled)
            self.assertTrue(next(x for x in at.button if x.label == '대화 종료').disabled)
            next(x for x in at.button if x.label == '진행 대화 새로고침').click().run()
            self.assertEqual(at.session_state['ai_chat_messages'], messages)
            self.assertFalse(at.chat_input[0].disabled)
            self.assertEqual(history.call_count, 2)
            self.assertEqual(len(at.exception), 0)

    def test_changed_owner_restores_only_the_new_owners_history(self):
        at = self.chat()
        at.session_state['ai_chat_owner_id'] = 'old-owner'
        at.session_state['ai_chat_messages'] = [{'role': 'user', 'content': '이전 사용자 질문'}]
        messages = [{'role': 'user', 'content': '새 사용자 질문'}]
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.get_chat_history', return_value={'data': messages}) as history:
            at.run()
            self.assertEqual(at.session_state['ai_chat_messages'], messages)
            history.assert_called_once_with('fake-token')
            self.assertEqual(len(at.exception), 0)

    def test_summary_retry_keeps_request_id_and_success_clears_it(self):
        at = self.chat()
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.send_chat_message', return_value={'data': {'answer': '답변'}}), patch('views.chat.save_chat_summary', side_effect=[ChatAPIError('기록 정리 실패'), {'message': '저장 복구', 'data': {'remaining_messages': []}}]) as save:
            at.run()
            at.chat_input[0].set_value('질문').run()
            next(x for x in at.button if x.label == '대화 저장').click().run()
            request_id = at.session_state['ai_chat_save_request_id']
            self.assertEqual(len(at.session_state['ai_chat_messages']), 2)
            next(x for x in at.button if x.label == '대화 저장').click().run()
            self.assertEqual(save.call_args_list[0].kwargs['request_id'], request_id)
            self.assertEqual(save.call_args_list[1].kwargs['request_id'], request_id)
            self.assertNotIn('ai_chat_save_request_id', at.session_state)
            self.assertEqual(at.session_state['ai_chat_messages'], [])
            self.assertEqual(len(at.exception), 0)

    def test_new_question_after_failed_save_starts_a_new_request_id(self):
        at = self.chat()
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.send_chat_message', return_value={'data': {'answer': '답변'}}), patch('views.chat.save_chat_summary', side_effect=ChatAPIError('저장 실패')) as save:
            at.run()
            at.chat_input[0].set_value('첫 질문').run()
            next(x for x in at.button if x.label == '대화 저장').click().run()
            first = save.call_args.kwargs['request_id']
            at.chat_input[0].set_value('새 질문').run()
            next(x for x in at.button if x.label == '대화 저장').click().run()
            self.assertNotEqual(save.call_args.kwargs['request_id'], first)
            self.assertEqual(len(at.exception), 0)

    def test_active_history_refresh_loads_other_tab_and_failure_keeps_it(self):
        at = self.chat()
        latest = [{'role': 'user', 'content': '다른 탭의 질문'}]
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.get_chat_history', side_effect=[{'data': latest}, ChatAPIError('조회 실패')]) as refresh:
            at.run()
            next(x for x in at.button if x.label == '진행 대화 새로고침').click().run()
            self.assertEqual(at.session_state['ai_chat_messages'], latest)
            next(x for x in at.button if x.label == '진행 대화 새로고침').click().run()
            self.assertEqual(at.session_state['ai_chat_messages'], latest)
            self.assertTrue(any('조회 실패' in x.value for x in at.error))
            self.assertEqual(refresh.call_count, 2)
            self.assertEqual(len(at.exception), 0)

    def test_summary_save_restores_history_changed_during_generation(self):
        at = self.chat()
        remaining = [{'role': 'user', 'content': '다른 탭의 질문'}, {'role': 'assistant', 'content': '새 답변'}]
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), patch('views.chat.send_chat_message', return_value={'data': {'answer': '답변'}}), patch('views.chat.save_chat_summary', return_value={'message': '진행 기록 보존', 'data': {'remaining_messages': remaining}}):
            at.run()
            at.chat_input[0].set_value('질문').run()
            next(x for x in at.button if x.label == '대화 저장').click().run()
            self.assertEqual(at.session_state['ai_chat_messages'], remaining)
            self.assertTrue(any('기록 보존' in x.value for x in at.success))
            self.assertEqual(len(at.exception), 0)

    def chat(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app_pages/05_ai_chat.py'))
        at.session_state['loginout'] = 'login'
        at.session_state['user_id'] = 'test-owner'
        at.session_state['access_token'] = 'fake-token'
        at.session_state['ai_chat_owner_id'] = 'test-owner'
        at.session_state['ai_chat_history_attempted'] = True
        at.session_state['ai_chat_history_ready'] = True
        return at

    def test_chat_send_failure_preserves_messages_and_retry_succeeds(self):
        at = self.chat()
        with patch('views.chat.get_chat_profile', return_value={'data': {'nickname': '테스터'}}), \
             patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}), \
             patch('views.chat.send_chat_message', side_effect=[ChatAPIError('잠시 후 다시 시도'), {'data': {'answer': '안내 답변'}}]):
            at.run()
            at.chat_input[0].set_value('질문').run()
            self.assertEqual(at.session_state['ai_chat_messages'], [])
            self.assertTrue(any('잠시 후' in x.value for x in at.error))
            at.chat_input[0].set_value('질문').run()
            self.assertEqual(len(at.session_state['ai_chat_messages']), 2)
            next(x for x in at.button if x.label == '대화 종료').click().run()
            next(x for x in at.button if x.label == '취소').click().run()
            self.assertEqual(len(at.session_state['ai_chat_messages']), 2)
            self.assertEqual(len(at.exception), 0)

    def test_changed_owner_clears_previous_messages_and_notices(self):
        at = self.chat()
        at.session_state['ai_chat_owner_id'] = 'old-owner'
        at.session_state['ai_chat_messages'] = [{'role': 'user', 'content': '다른 사용자 상담'}]
        at.session_state['ai_chat_flash'] = '이전 사용자 안내'
        at.session_state['ai_chat_save_request_id'] = 'previous-user-request'
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), \
             patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}):
            at.run()
            self.assertEqual(at.session_state['ai_chat_messages'], [])
            self.assertEqual(len(at.success), 0)
            self.assertNotIn('ai_chat_save_request_id', at.session_state)
            self.assertEqual(len(at.exception), 0)

    def test_summary_selection_and_delete_cancel_preserve_saved_item(self):
        at = self.chat()
        item = {'id': 'summary-one', 'title': '가상 상담', 'summary': '확인할 요약 본문',
                'message_count': 2, 'model': 'mock-chat', 'created_at': '2026-10-01T01:00:00Z'}
        with patch('views.chat.get_chat_profile', return_value={'data': {}}), \
             patch('views.chat_summaries.get_chat_summaries', return_value={'data': [item]}), \
             patch('views.chat_summaries.delete_chat_summary') as delete:
            at.run()
            next(x for x in at.selectbox if x.label == '확인할 상담').select('summary-one').run()
            self.assertTrue(any('확인할 요약 본문' in x.value for x in at.markdown))
            next(x for x in at.button if x.label == '✕').click().run()
            next(x for x in at.button if x.label == '삭제 취소').click().run()
            delete.assert_not_called()
            self.assertEqual(at.session_state['ai_chat_selected_summary'], 'summary-one')
            self.assertEqual(len(at.exception), 0)

    def test_location_missing_address_stops_before_provider_call(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app_pages/06_location.py'))
        with patch('views.location.search_location_listings', return_value={'data': {'items': [{'id': 1, 'title': '가상 주택'}]}}), \
             patch('views.location.geocode_location') as geocode:
            at.run()
            at.text_input[0].set_value('가상')
            next(x for x in at.button if x.label == '주변생활권 탐색').click().run()
            geocode.assert_not_called()
            self.assertTrue(any('상세주소' in x.value for x in at.error))
            self.assertEqual(len(at.exception), 0)

    def test_summary_reuses_success_then_refresh_and_save_reload(self):
        at = self.chat()
        at.session_state['ai_chat_owner_id'] = 'test-owner'
        at.session_state['ai_chat_messages'] = [{'role': 'user', 'content': '가상 질문'}, {'role': 'assistant', 'content': '가상 답변'}]
        with patch('views.chat.get_chat_profile', return_value={'data': {}}) as profile, \
             patch('views.chat_summaries.get_chat_summaries', return_value={'data': []}) as summaries, \
             patch('views.chat.save_chat_summary', return_value={'message': '저장 성공'}):
            at.run(); at.run()
            self.assertEqual(summaries.call_count, 1)
            self.assertEqual(profile.call_count, 1)
            next(x for x in at.button if x.label == '상담 목록 새로고침').click().run()
            self.assertEqual(summaries.call_count, 2)
            next(x for x in at.button if x.label == '대화 저장').click().run()
            self.assertEqual(summaries.call_count, 3)
            self.assertEqual(at.session_state['ai_chat_messages'], [])
            self.assertEqual(len(at.exception), 0)

    def test_location_rerun_reuses_result_and_refresh_reloads(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app_pages/06_location.py'))
        item = {'id': 1, 'title': '가상 주택', 'detail_address': '검증용 가상 주소'}
        with patch('views.location.search_location_listings', return_value={'data': {'items': [item]}}), \
             patch('views.location.geocode_location', return_value={'data': {'latitude': 37.5, 'longitude': 127.0}}) as geo, \
             patch('views.location.get_nearby_facilities', return_value={'data': {}}) as facilities:
            at.run(); at.text_input[0].set_value('가상')
            next(x for x in at.button if x.label == '주변생활권 탐색').click().run()
            at.run(); at.run()
            self.assertEqual(geo.call_count, 1)
            self.assertEqual(facilities.call_count, 1)
            next(x for x in at.button if x.label == '생활권 결과 새로고침').click().run()
            self.assertEqual(facilities.call_count, 2)
            self.assertEqual(len(at.exception), 0)

    def test_candidate_page_navigation_replaces_options(self):
        at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app_pages/06_location.py'))
        def candidates(query, page=1):
            return {'data': {'items': [{'id': page, 'title': f'가상 {page}', 'detail_address': ''}], 'page': page, 'total_pages': 2, 'total_count': 21}}
        with patch('views.location.search_location_listings', side_effect=candidates) as search:
            at.run(); at.text_input[0].set_value('가상')
            next(x for x in at.button if x.label == '주변생활권 탐색').click().run()
            next(x for x in at.button if x.label == '다음 후보').click().run()
            self.assertEqual(search.call_args.args, ('가상', 2))
            self.assertEqual(at.session_state['location-search-matches'][0]['id'], 2)
            self.assertEqual(len(at.exception), 0)
