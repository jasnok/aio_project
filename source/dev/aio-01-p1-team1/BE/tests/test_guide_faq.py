"""표시된 FAQ는 공급자 없이 응답하고 자유 질문은 기존 경로를 사용한다."""
import unittest
from unittest.mock import Mock, patch

from housing_common.guide_faq import SITE_GUIDE_FAQ
from app.services import guide_service


class GuideFaqTest(unittest.TestCase):
    def test_all_displayed_site_questions_work_without_provider_configuration(self):
        with (
            patch.object(guide_service, "get_gemini_mode", side_effect=RuntimeError("no config")),
            patch.object(guide_service, "get_gemini_client") as factory,
        ):
            for question, category in SITE_GUIDE_FAQ.items():
                with self.subTest(question=question):
                    answer = guide_service.create_guide_answer([], f"  {question}  ")
                    self.assertEqual(answer.category.value, category)
                    self.assertEqual(answer.response_type, "guide")
                    self.assertTrue(answer.steps)
                    self.assertEqual(answer.model, "rule-guide")
            factory.assert_not_called()

    def test_extra_request_does_not_match_faq_as_substring(self):
        question = next(iter(SITE_GUIDE_FAQ)) + " 그리고 신청 자격도 판단해줘"
        with patch.object(guide_service, "get_gemini_client") as factory:
            answer = guide_service.create_guide_answer([], question)
        self.assertEqual(answer.response_type, "refusal")
        factory.assert_not_called()

    def test_term_question_still_uses_provider_and_validated_answer(self):
        client = Mock()
        client.models.generate_content.return_value.text = (
            '{"category":"TERM_EXPLANATION","confidence":0.9,"short_answer":"임대 보증금 설명"}'
        )
        with (
            patch.object(guide_service, "get_gemini_mode", return_value="gemini"),
            patch.object(guide_service, "get_gemini_model", return_value="test-model"),
            patch.object(guide_service, "get_gemini_client", return_value=client),
        ):
            answer = guide_service.create_guide_answer([], "보증금이 무엇인가요?")
        client.models.generate_content.assert_called_once()
        client.close.assert_called_once()
        self.assertEqual(answer.answer, "임대 보증금 설명")
        self.assertEqual(answer.model, "test-model")
