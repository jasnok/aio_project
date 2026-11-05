from app.schemas.chat_schema import ChatHistorySnapshot
import json
import os
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.core import workflow_trace
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.exceptions.handlers import register_exception_handlers
from app.routers import chat_router as router
from app.schemas.chat_schema import ChatMessage
from app.services import chat_service


class ChatWorkflowTraceTests(unittest.TestCase):
    def setUp(self):
        chat_service._preview_summaries.clear()
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router.chat_router)
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id="private-user-id", email="private@example.invalid")
        self.client = TestClient(app)
        self.history = [ChatMessage(role="user", content="private-question"), ChatMessage(role="assistant", content="private-answer")]

    def events(self, log):
        return [json.loads(call.kwargs["message"]) for call in log.call_args_list]

    def test_answer_success_links_stages_and_never_logs_user_or_content(self):
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock"}), patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=[])), patch.object(router, "append_chat_exchange"), patch.object(workflow_trace, "add_log") as log:
            response = self.client.post("/chat/message", json={"question": "private-question"})
        self.assertEqual(response.status_code, 200)
        events = self.events(log)
        completed = [event["stage"] for event in events if event["status"] == "completed"]
        self.assertEqual(completed, ["history.read", "answer.mock", "answer.validate", "history.append", "workflow"])
        self.assertEqual(len({event["trace_id"] for event in events}), 1)
        self.assertNotIn("private", " ".join(call.kwargs["message"] for call in log.call_args_list))

    def test_invalid_provider_output_identifies_validation_and_skips_storage(self):
        provider = Mock()
        provider.models.generate_content.return_value.text = "private-output" * 1000
        with patch.object(chat_service, "get_gemini_mode", return_value="gemini"), patch.object(chat_service, "get_gemini_client", return_value=provider), patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=[])), patch.object(router, "append_chat_exchange") as append, patch.object(workflow_trace, "add_log") as log:
            response = self.client.post("/chat/message", json={"question": "private-question"})
        self.assertEqual(response.status_code, 502)
        failed = [event for event in self.events(log) if event["status"] == "failed"]
        self.assertEqual(failed[0]["stage"], "answer.validate")
        self.assertEqual(failed[0]["reason"], "invalid_response")
        self.assertEqual(failed[-1]["stage"], "workflow")
        self.assertFalse(any(event["stage"] == "history.append" for event in self.events(log)))
        append.assert_not_called()

    def test_summary_storage_failure_identifies_persist_and_skips_cleanup(self):
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock"}), patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=self.history)), patch.object(chat_service, "persist_chat_summary", side_effect=HTTPException(500, "private storage detail")), patch.object(router, "clear_summarized_history") as cleanup, patch.object(workflow_trace, "add_log") as log:
            response = self.client.post("/chat/save", json={})
        self.assertEqual(response.status_code, 500)
        failed = [event for event in self.events(log) if event["status"] == "failed"]
        self.assertEqual(failed[0]["stage"], "summary.persist")
        cleanup.assert_not_called()
        self.assertNotIn("private", " ".join(call.kwargs["message"] for call in log.call_args_list))

    def test_summary_recovery_does_not_record_a_new_generation_or_delete(self):
        request_id = uuid4()
        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock", "CHAT_SUMMARY_STORAGE": "preview"}):
            chat_service.create_chat_summary("private-user-id", self.history, request_id)
            with patch.object(router, "get_chat_snapshot", return_value=ChatHistorySnapshot(messages=self.history)), patch.object(router, "clear_summarized_history") as cleanup, patch.object(workflow_trace, "add_log") as log:
                response = self.client.post("/chat/save", json={"request_id": str(request_id)})
        self.assertEqual(response.status_code, 200)
        stages = {event["stage"] for event in self.events(log)}
        self.assertIn("summary.recover", stages)
        self.assertNotIn("summary.provider", stages)
        self.assertNotIn("summary.mock", stages)
        self.assertNotIn("history.cleanup", stages)
        cleanup.assert_not_called()
