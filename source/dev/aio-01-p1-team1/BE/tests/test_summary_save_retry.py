from app.schemas.chat_schema import ChatHistorySnapshot
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.exceptions.handlers import register_exception_handlers
from app.routers import chat_router as router
from app.schemas.chat_schema import ChatMessage
from app.services import chat_service


class SummarySaveRetryTests(unittest.TestCase):
    def setUp(self):
        chat_service._preview_summaries.clear()
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router.chat_router)
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id="retry-test", email="test@example.invalid")
        self.client = TestClient(app)
        self.history = [ChatMessage(role="user", content="질문"), ChatMessage(role="assistant", content="답변")]
        self.request_id = uuid4()

    def test_save_then_redis_failure_retry_recovers_one_summary_without_new_generation(self):
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock", "CHAT_SUMMARY_STORAGE": "preview"}), patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=self.history)), patch.object(router, "clear_summarized_history", side_effect=HTTPException(503, "기록 정리 실패")) as clear, patch.object(router, "create_chat_summary", wraps=chat_service.create_chat_summary) as generate:
            first = self.client.post("/chat/save", json={"request_id": str(self.request_id)})
            second = self.client.post("/chat/save", json={"request_id": str(self.request_id)})
            self.assertEqual(len(chat_service.list_chat_summaries("retry-test")), 1)
        self.assertEqual(first.status_code, 503)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["data"]["id"], str(self.request_id))
        self.assertEqual(len(second.json()["data"]["remaining_messages"]), 2)
        generate.assert_called_once()
        clear.assert_called_once()

    def test_completed_request_replay_returns_same_id_even_without_active_messages(self):
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock", "CHAT_SUMMARY_STORAGE": "preview"}), patch.object(router, "get_chat_snapshot", side_effect=[ChatHistorySnapshot(messages=self.history), ChatHistorySnapshot()]), patch.object(router, "clear_summarized_history", return_value=[]), patch.object(router, "create_chat_summary", wraps=chat_service.create_chat_summary) as generate:
            first = self.client.post("/chat/save", json={"request_id": str(self.request_id)})
            second = self.client.post("/chat/save", json={"request_id": str(self.request_id)})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["data"]["id"], second.json()["data"]["id"])
        generate.assert_called_once()

    def test_existing_summary_of_other_user_is_not_returned(self):
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock", "CHAT_SUMMARY_STORAGE": "preview"}):
            chat_service.create_chat_summary("other-user", self.history, self.request_id)
            self.assertIsNone(chat_service.get_chat_summary("retry-test", self.request_id))

    def test_preview_persistence_deduplicates_same_id(self):
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock", "CHAT_SUMMARY_STORAGE": "preview"}):
            first = chat_service.create_chat_summary("retry-test", self.history, self.request_id)
            second = chat_service.create_chat_summary("retry-test", self.history, self.request_id)
            self.assertEqual(len(chat_service.list_chat_summaries("retry-test")), 1)
            self.assertEqual(first, second)

    def test_supabase_lookup_filters_both_request_id_and_owner(self):
        database = Mock()
        query = database.table.return_value.select.return_value
        query.eq.return_value = query
        query.limit.return_value = query
        query.execute.return_value = SimpleNamespace(data=[])
        with patch.object(chat_service, "get_summary_storage_mode", return_value="supabase"), patch.object(chat_service, "get_supabase", return_value=database):
            self.assertIsNone(chat_service.get_chat_summary("retry-test", self.request_id))
        self.assertEqual(query.eq.call_args_list[0].args, ("id", str(self.request_id)))
        self.assertEqual(query.eq.call_args_list[1].args, ("user_id", "retry-test"))

    def test_invalid_request_id_is_rejected_before_generation(self):
        with patch.object(router, "create_chat_summary") as generate:
            response = self.client.post("/chat/save", json={"request_id": "not-a-uuid"})
        self.assertEqual(response.status_code, 422)
        generate.assert_not_called()
