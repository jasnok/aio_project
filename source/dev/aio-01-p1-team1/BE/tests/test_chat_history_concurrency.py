import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from redis.exceptions import WatchError

from app.schemas.chat_schema import ChatMessage
from app.services import chat_history_service as service
from test_chat_history_service import FakeRedis


class ChatHistoryConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeRedis()

    def test_watch_conflict_reloads_new_history_instead_of_overwriting_it(self):
        first = self.store.pipeline()
        execute = first.execute
        def collide():
            service.save_chat_history("user", [ChatMessage(role="user", content="other question"), ChatMessage(role="assistant", content="other answer")], self.store)
            execute()
        first.execute = collide
        later = self.store.pipeline()
        with patch.object(self.store, "pipeline", side_effect=[first, later]):
            saved = service.append_chat_exchange("user", "question", "answer", self.store)
        self.assertEqual([item.content for item in saved], ["other question", "other answer", "question", "answer"])
        self.assertEqual(len(service.get_chat_history("user", self.store)), 4)

    def test_changed_generation_context_rejects_append_and_preserves_record(self):
        history = service.append_chat_exchange("user", "first", "answer", self.store)
        service.append_chat_exchange("user", "second", "answer", self.store)
        with self.assertRaises(HTTPException) as caught:
            service.append_chat_exchange("user", "stale", "answer", self.store, expected_history=history)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(len(service.get_chat_history("user", self.store)), 4)

    def test_matching_summary_snapshot_is_deleted(self):
        history = service.append_chat_exchange("user", "first", "answer", self.store)
        self.assertEqual(service.clear_summarized_history("user", history, self.store), [])
        self.assertEqual(service.get_chat_history("user", self.store), [])

    def test_changed_summary_snapshot_is_returned_without_deleting_or_resetting_ttl(self):
        history = service.append_chat_exchange("user", "first", "answer", self.store)
        current = service.append_chat_exchange("user", "second", "answer", self.store)
        version = self.store.version
        self.assertEqual(service.clear_summarized_history("user", history, self.store), current)
        self.assertEqual(self.store.version, version)

    def test_new_exchange_during_snapshot_delete_is_preserved_after_watch_retry(self):
        history = service.append_chat_exchange("user", "first", "answer", self.store)
        first = self.store.pipeline()
        execute = first.execute
        def collide():
            service.save_chat_history("user", [*history, ChatMessage(role="user", content="new")], self.store)
            execute()
        first.execute = collide
        with patch.object(self.store, "pipeline", side_effect=[first, self.store.pipeline()]):
            remaining = service.clear_summarized_history("user", history, self.store)
        self.assertEqual(len(remaining), 3)
        self.assertEqual(remaining[-1].content, "new")

    def test_conflicts_stop_after_three_attempts_without_provider_retry(self):
        pipelines = [self.store.pipeline() for _ in range(3)]
        for pipe in pipelines:
            pipe.execute = Mock(side_effect=WatchError())
        with patch.object(self.store, "pipeline", side_effect=pipelines) as factory:
            with self.assertRaises(HTTPException) as caught:
                service.append_chat_exchange("user", "question", "answer", self.store)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(factory.call_count, 3)
        self.assertEqual(service.get_chat_history("user", self.store), [])

    def test_atomic_append_retains_limit_and_ttl(self):
        with patch.object(service, "get_chat_history_max_messages", return_value=2), patch.object(service, "get_chat_history_ttl", return_value=60):
            service.append_chat_exchange("user", "first", "answer", self.store)
            saved = service.append_chat_exchange("user", "second", "answer", self.store)
        self.assertEqual([item.content for item in saved], ["second", "answer"])
        self.assertEqual(self.store.expirations["ai-chat:active:user"], 60)
