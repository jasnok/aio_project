import json
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.exceptions.handlers import register_exception_handlers
from app.routers import chat_router as router
from app.schemas.chat_schema import ChatMessage
from app.services import chat_history_service as service, chat_service
from test_chat_history_service import FakeRedis


class ChatHistoryRevisionTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeRedis()

    def test_empty_history_ended_during_generation_cannot_be_recreated(self):
        original = service.get_chat_snapshot('user', self.store)
        service.delete_chat_history('user', self.store)
        with self.assertRaises(HTTPException) as caught:
            service.append_chat_exchange('user', 'late question', 'late answer', self.store, expected_history=original.messages, expected_revision=original.revision)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(service.get_chat_history('user', self.store), [])
        self.assertGreater(self.store.expirations['ai-chat:active:user'], 0)

    def test_identical_new_conversation_is_not_deleted_by_old_summary(self):
        service.append_chat_exchange('user', 'question', 'answer', self.store)
        original = service.get_chat_snapshot('user', self.store)
        service.delete_chat_history('user', self.store)
        service.append_chat_exchange('user', 'question', 'answer', self.store)
        current = service.get_chat_snapshot('user', self.store)
        version = self.store.version
        remaining = service.clear_summarized_history('user', original.messages, self.store, expected_revision=original.revision)
        self.assertEqual(remaining, original.messages)
        self.assertNotEqual(original.revision, current.revision)
        self.assertEqual(self.store.version, version)

    def test_legacy_list_is_read_and_upgraded_without_losing_messages(self):
        original = [ChatMessage(role='user', content='legacy question'), ChatMessage(role='assistant', content='legacy answer')]
        self.store.set('ai-chat:active:user', json.dumps([item.model_dump() for item in original]), ex=3600)
        snapshot = service.get_chat_snapshot('user', self.store)
        self.assertIsNone(snapshot.revision)
        self.assertEqual(snapshot.messages, original)
        service.append_chat_exchange('user', 'new question', 'new answer', self.store, expected_history=snapshot.messages, expected_revision=snapshot.revision)
        updated = service.get_chat_snapshot('user', self.store)
        self.assertIsNotNone(updated.revision)
        self.assertEqual(updated.messages[:2], original)
        self.assertEqual(len(updated.messages), 4)

    def test_matching_summary_clears_messages_but_invalidates_old_revision(self):
        service.append_chat_exchange('user', 'question', 'answer', self.store)
        original = service.get_chat_snapshot('user', self.store)
        self.assertEqual(service.clear_summarized_history('user', original.messages, self.store, expected_revision=original.revision), [])
        current = service.get_chat_snapshot('user', self.store)
        self.assertEqual(current.messages, [])
        self.assertNotEqual(current.revision, original.revision)

    def test_router_propagates_snapshot_revision_without_exposing_it_in_history(self):
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router.chat_router)
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id='user', email='test@example.invalid')
        client = TestClient(app)
        def generate(messages, question, trace=None):
            answer = chat_service.create_chat_answer(messages, question, trace=trace)
            service.delete_chat_history('user', self.store)
            return answer
        with patch.object(service, 'get_redis', return_value=self.store), patch.object(chat_service, 'get_gemini_mode', return_value='mock'), patch.object(router, 'create_chat_answer', side_effect=generate) as provider:
            response = client.post('/chat/message', json={'question': 'late question'})
            history = client.get('/chat/history')
        self.assertEqual(response.status_code, 409)
        provider.assert_called_once()
        self.assertEqual(history.json()['data'], [])
        self.assertNotIn('revision', history.text)

    def test_summary_router_preserves_identical_conversation_started_during_generation(self):
        service.append_chat_exchange('user', 'question', 'answer', self.store)
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(router.chat_router)
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(id='user', email='test@example.invalid')
        def generate(user_id, messages, summary_id=None, trace=None):
            summary = chat_service.create_chat_summary(user_id, messages, summary_id=summary_id, trace=trace)
            service.delete_chat_history(user_id, self.store)
            service.append_chat_exchange(user_id, 'question', 'answer', self.store)
            return summary
        with patch.object(service, 'get_redis', return_value=self.store), patch.object(chat_service, 'get_gemini_mode', return_value='mock'), patch.object(chat_service, 'persist_chat_summary', side_effect=lambda item: item), patch.object(router, 'create_chat_summary', side_effect=generate):
            response = TestClient(app).post('/chat/save', json={})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']['remaining_messages']), 2)
        self.assertEqual(len(service.get_chat_history('user', self.store)), 2)
        self.assertIn('보존', response.json()['message'])
