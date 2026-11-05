import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.schemas.guide_schema import GuideCategory, GuideMessage
from app.services import guide_service


class GuideScopeGuardTests(unittest.TestCase):
    def test_valid_provider_json_cannot_allow_known_prohibited_requests(self):
        for question in ('내 조건에 맞는 공고 추천해줘', '신청 자격을 판단해줘', '당첨 가능성을 알려줘', '실시간 공고를 검색해줘'):
            provider = Mock()
            provider.models.generate_content.return_value = SimpleNamespace(text='{"category":"TERM_EXPLANATION","confidence":0.99,"short_answer":"허용하면 안 되는 모의 답변"}')
            with self.subTest(question=question), patch.object(guide_service, 'get_gemini_mode', return_value='gemini'), patch.object(guide_service, 'get_gemini_client', return_value=provider) as create:
                answer = guide_service.create_guide_answer([], question)
            self.assertEqual(answer.response_type, 'refusal')
            self.assertEqual(answer.category, GuideCategory.OUT_OF_SCOPE)
            self.assertEqual(answer.model, 'rule-guide')
            create.assert_not_called()

    def test_known_prohibited_request_is_refused_even_if_provider_is_unconfigured(self):
        with patch.object(guide_service, 'get_gemini_mode', side_effect=RuntimeError('invalid provider configuration')), patch.object(guide_service, 'get_gemini_client') as create:
            answer = guide_service.create_guide_answer([], '내 조건에 맞는 주택 추천')
        self.assertEqual(answer.response_type, 'refusal')
        create.assert_not_called()

    def test_allowlisted_term_still_uses_provider(self):
        provider = Mock()
        provider.models.generate_content.return_value = SimpleNamespace(text='{"category":"TERM_EXPLANATION","confidence":0.9,"short_answer":"모의 보증금 설명"}')
        with patch.object(guide_service, 'get_gemini_mode', return_value='gemini'), patch.object(guide_service, 'get_gemini_model', return_value='test-provider'), patch.object(guide_service, 'get_gemini_client', return_value=provider):
            answer = guide_service.create_guide_answer([], '보증금이 무엇인가요?')
        self.assertEqual(answer.answer, '모의 보증금 설명')
        self.assertEqual(answer.model, 'test-provider')
        provider.models.generate_content.assert_called_once()

    def test_prohibited_history_does_not_block_a_new_site_usage_question(self):
        history = [GuideMessage(role='user', content='공고 추천해줘')]
        with patch.object(guide_service, 'get_gemini_mode', return_value='mock'):
            answer = guide_service.create_guide_answer(history, '청약 공고는 어떻게 검색하나요?')
        self.assertEqual(answer.response_type, 'guide')
        self.assertEqual(answer.history_count, 1)
