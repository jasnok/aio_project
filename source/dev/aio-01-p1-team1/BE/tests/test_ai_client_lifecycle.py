import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from app.core.external_error import ExternalServiceError
from app.schemas.chat_schema import ChatMessage
from app.services import chat_service, guide_service


class AIClientLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.history = [ChatMessage(role="user", content="질문"), ChatMessage(role="assistant", content="답변")]

    def calls(self):
        return [(chat_service, lambda: chat_service._generate_text([], "prompt"), "답변"),
                (chat_service, lambda: chat_service._generate_summary(self.history), '{"summary":"요약"}'),
                (guide_service, lambda: guide_service.classify_question([], "unknown question"), '{"category":"OUT_OF_SCOPE","confidence":0.9}')]

    def test_each_provider_client_closes_after_success(self):
        for module, call, text in self.calls():
            provider = Mock()
            provider.models.generate_content.return_value = SimpleNamespace(text=text)
            with self.subTest(module=module.__name__), patch.object(module, "get_gemini_mode", return_value="gemini"), patch.object(module, "get_gemini_client", return_value=provider):
                call()
            provider.close.assert_called_once()

    def test_each_provider_client_closes_after_timeout(self):
        for module, call, text in self.calls():
            provider = Mock()
            provider.models.generate_content.side_effect = httpx.ReadTimeout("private provider detail")
            with self.subTest(module=module.__name__), patch.object(module, "get_gemini_mode", return_value="gemini"), patch.object(module, "get_gemini_client", return_value=provider):
                with self.assertRaises(ExternalServiceError) as caught:
                    call()
            self.assertEqual(caught.exception.status_code, 504)
            provider.close.assert_called_once()

    def test_summary_client_is_closed_before_output_validation_failure(self):
        provider = Mock()
        provider.models.generate_content.return_value = SimpleNamespace(text="not-json")
        with patch.object(chat_service, "get_gemini_client", return_value=provider):
            with self.assertRaises(ExternalServiceError):
                chat_service._generate_summary(self.history)
        provider.close.assert_called_once()

    def test_non_string_guide_output_uses_safe_clarification_path(self):
        for text in ({"private": "input"}, 123, None):
            provider = Mock()
            provider.models.generate_content.return_value = SimpleNamespace(text=text)
            with self.subTest(text=text), patch.object(guide_service, "get_gemini_mode", return_value="gemini"), patch.object(guide_service, "get_gemini_client", return_value=provider):
                result = guide_service.create_guide_answer([], "unknown question")
            self.assertEqual(result.response_type, "clarification")
            self.assertNotIn("private", result.answer)
            provider.close.assert_called_once()

    def test_mock_mode_does_not_create_real_provider_clients(self):
        with patch.object(chat_service, "get_gemini_mode", return_value="mock"), patch.object(chat_service, "get_gemini_client") as chat_client, patch.object(guide_service, "get_gemini_mode", return_value="mock"), patch.object(guide_service, "get_gemini_client") as guide_client:
            chat_service.create_chat_answer([], "질문")
            guide_service.create_guide_answer([], "unknown question")
        chat_client.assert_not_called()
        guide_client.assert_not_called()
