"""외부 LLM 없이 저장 직전의 출력 검증과 실패 후 기록 보존을 확인합니다."""
from app.schemas.chat_schema import ChatHistorySnapshot
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.core.external_error import ExternalServiceError
from app.core import gemini_config
from app.exceptions.handlers import register_exception_handlers
from app.routers import chat_router as router
from app.schemas.chat_schema import ChatAnswer, ChatMessage, ChatSummaryDraft
from app.services import chat_service


class ChatOutputContractTests(unittest.TestCase):
    def setUp(self):
        self.provider = Mock()
        self.messages = [ChatMessage(role="user", content="질문"), ChatMessage(role="assistant", content="답변")]

    def summary(self, text):
        self.provider.models.generate_content.return_value = SimpleNamespace(text=text)
        with patch.object(chat_service, "get_gemini_client", return_value=self.provider):
            return chat_service._generate_summary(self.messages)

    def test_answer_boundary_can_be_stored_without_changes(self):
        answer = ChatAnswer(answer="가" * 4000, model="test", history_count=0)
        self.assertEqual(ChatMessage(role="assistant", content=answer.answer).content, answer.answer)
        for text in ("가" * 4001, "   "):
            with self.subTest(length=len(text)), self.assertRaises(ValidationError):
                ChatAnswer(answer=text, model="test", history_count=0)

    def test_generated_oversized_answer_is_a_safe_provider_error(self):
        self.provider.models.generate_content.return_value = SimpleNamespace(text="private-output-" * 400)
        with patch.object(chat_service, "get_gemini_mode", return_value="gemini"), patch.object(chat_service, "get_gemini_client", return_value=self.provider):
            with self.assertRaises(ExternalServiceError) as caught:
                chat_service.create_chat_answer([], "질문")
        self.assertEqual(caught.exception.reason, "invalid_response")
        self.assertNotIn("private-output", caught.exception.detail)

    def test_non_string_answer_does_not_crash_during_strip(self):
        for text in ({"private": "value"}, 123, None):
            self.provider.models.generate_content.return_value = SimpleNamespace(text=text)
            with self.subTest(text=text), patch.object(chat_service, "get_gemini_client", return_value=self.provider):
                with self.assertRaises(ExternalServiceError):
                    chat_service._generate_text([], "prompt")

    def test_structured_summary_and_schema_are_sent(self):
        self.assertEqual(self.summary('{"title":" 상담 제목 ","summary":" 요약 내용 "}'), ("상담 제목", "요약 내용"))
        config = self.provider.models.generate_content.call_args.kwargs["config"]
        self.assertIs(config["response_schema"], ChatSummaryDraft)
        self.assertEqual(config["response_mime_type"], "application/json")

    def test_missing_title_keeps_existing_title_fallback(self):
        self.assertEqual(self.summary('{"summary":"상담 주제:\\n- 청약 신청"}'), ("청약 신청", "상담 주제:\n- 청약 신청"))

    def test_invalid_json_types_and_blank_summary_are_rejected(self):
        invalid = ["not-json", "[]", "null", None,
                   json.dumps({"title": {"private": "value"}, "summary": ["private"]}),
                   '{"title":"제목","summary":123}', '{"title":"제목"}',
                   '{"summary":"  "}', '{"summary":"요약","unexpected":"private"}']
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ExternalServiceError) as caught:
                self.summary(payload)
            self.assertEqual(caught.exception.status_code, 502)
            self.assertEqual(caught.exception.reason, "invalid_response")
            self.assertNotIn("private", caught.exception.detail)

    def test_timeout_remains_distinct_from_validation_failure(self):
        self.provider.models.generate_content.side_effect = httpx.ReadTimeout("private provider detail")
        with patch.object(chat_service, "get_gemini_client", return_value=self.provider):
            with self.assertRaises(ExternalServiceError) as caught:
                chat_service._generate_summary(self.messages)
        self.assertEqual(caught.exception.status_code, 504)
        self.assertEqual(caught.exception.reason, "timeout")


class ChatOutputRouterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router.chat_router)
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id="contract-test", email="test@example.invalid")
        self.client = TestClient(app)
        self.provider = Mock()

    def test_rejected_answer_does_not_append_history(self):
        self.provider.models.generate_content.return_value.text = "private" * 1000
        with patch.object(chat_service, "get_gemini_mode", return_value="gemini"), patch.object(chat_service, "get_gemini_client", return_value=self.provider), patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=[])), patch.object(router, "append_chat_exchange") as append:
            response = self.client.post("/chat/message", json={"question": "질문"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["code"], "invalid_response")
        self.assertNotIn("private", response.text)
        append.assert_not_called()

    def test_rejected_summary_does_not_save_or_delete_active_history(self):
        self.provider.models.generate_content.return_value.text = '{"summary":{"private":"input"}}'
        history = [ChatMessage(role="user", content="질문"), ChatMessage(role="assistant", content="답변")]
        with patch.object(chat_service, "get_gemini_mode", return_value="gemini"), patch.object(chat_service, "get_gemini_client", return_value=self.provider), patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=history)), patch.object(chat_service, "persist_chat_summary") as persist, patch.object(router, "clear_summarized_history") as clear:
            response = self.client.post("/chat/save", json={})
        self.assertEqual(response.status_code, 502)
        persist.assert_not_called()
        clear.assert_not_called()


class GeminiCallOptionsTests(unittest.TestCase):
    def test_installed_sdk_can_serialize_contract_without_external_network(self):
        from google import genai
        from google.genai import types

        requests = []
        def respond(request):
            requests.append(json.loads(request.content))
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"title":"제목","summary":"요약"}'}], "role": "model"}, "finishReason": "STOP"}]})
        with httpx.Client(transport=httpx.MockTransport(respond)) as transport:
            with genai.Client(api_key="test-only-key", http_options=types.HttpOptions(httpx_client=transport, retry_options=types.HttpRetryOptions(attempts=1))) as provider:
                response = provider.models.generate_content(model="gemini-2.5-flash-lite", contents="test", config={"response_mime_type": "application/json", "response_schema": ChatSummaryDraft})
        self.assertEqual(ChatSummaryDraft.model_validate_json(response.text).summary, "요약")
        schema = requests[0]["generationConfig"]["responseSchema"]
        self.assertIn("summary", schema["required"])

    def test_sdk_receives_timeout_in_milliseconds_and_one_attempt(self):
        with patch.object(gemini_config, "get_chat_setting", return_value="test-only-key"), patch("google.genai.Client") as factory:
            gemini_config.get_gemini_client()
        options = factory.call_args.kwargs["http_options"]
        self.assertEqual(options.timeout, 30_000)
        self.assertEqual(options.retry_options.attempts, 1)

    def test_missing_key_never_constructs_provider_client(self):
        with patch.object(gemini_config, "get_chat_setting", return_value=""), patch("google.genai.Client") as factory:
            with self.assertRaises(RuntimeError):
                gemini_config.get_gemini_client()
        factory.assert_not_called()
