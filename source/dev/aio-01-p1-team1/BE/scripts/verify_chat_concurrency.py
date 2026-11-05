"""로컬 Redis에서 임시 UUID 키로 충돌·요약 기록 보존을 검증합니다."""
import sys
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from fastapi import HTTPException
import redis
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'BE'))
from app.services.chat_history_service import append_chat_exchange, get_chat_history, get_chat_snapshot, clear_summarized_history, delete_chat_history

user = 'atomic-check-' + uuid4().hex
key = 'ai-chat:active:' + user
client = redis.Redis.from_url('redis://127.0.0.1:16379/0', decode_responses=True)
barrier = threading.Barrier(2)
local = threading.local()

class RacePipeline:
    def __init__(self, pipe):
        self.pipe = pipe
    def __enter__(self):
        self.pipe.__enter__()
        return self
    def __exit__(self, *args):
        return self.pipe.__exit__(*args)
    def __getattr__(self, name):
        return getattr(self.pipe, name)
    def get(self, name):
        value = self.pipe.get(name)
        if not getattr(local, 'read_once', False):
            local.read_once = True
            barrier.wait(timeout=5)
        return value

class RaceClient:
    def pipeline(self):
        return RacePipeline(client.pipeline())

if client.exists(key):
    client.close()
    raise RuntimeError('Temporary key already exists; nothing was changed')
try:
    with patch('app.services.chat_history_service.get_chat_history_max_messages', return_value=30), patch('app.services.chat_history_service.get_chat_history_ttl', return_value=3600):
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(append_chat_exchange, user, f'question-{i}', f'answer-{i}', RaceClient()) for i in range(2)]
            for result in futures:
                result.result()
        history = get_chat_history(user, client)
        assert len(history) == 4
        assert 3500 <= client.ttl(key) <= 3600
        append_chat_exchange(user, 'new question', 'new answer', client)
        remaining = clear_summarized_history(user, history, client)
        assert len(remaining) == len(get_chat_history(user, client)) == 6
        assert clear_summarized_history(user, remaining, client) == []
        assert get_chat_history(user, client) == []
        assert client.exists(key) and client.ttl(key) > 0  # 내용 없는 revision도 만료됩니다.
        snapshot = get_chat_snapshot(user, client)
        delete_chat_history(user, client)
        try:
            append_chat_exchange(user, 'late question', 'late answer', client, expected_history=snapshot.messages, expected_revision=snapshot.revision)
        except HTTPException as error:
            assert error.status_code == 409
        else:
            raise AssertionError('Ended conversation was recreated')
        assert get_chat_history(user, client) == []
        append_chat_exchange(user, 'same question', 'same answer', client)
        old = get_chat_snapshot(user, client)
        delete_chat_history(user, client)
        append_chat_exchange(user, 'same question', 'same answer', client)
        preserved = clear_summarized_history(user, old.messages, client, expected_revision=old.revision)
        assert preserved == old.messages == get_chat_history(user, client)
    result = {'concurrent_exchanges': 2, 'stored_messages': 4, 'changed_snapshot_messages_preserved': 6, 'matching_snapshot_messages_cleared': True, 'ended_conversation_late_answer_rejected': True, 'identical_new_conversation_preserved': True, 'scope': 'Actual local Redis on loopback; own disposable UUID key; no LLM calls'}
finally:
    client.delete(key)
    client.close()
output = root / '.runtime/chat-atomic-validation.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
