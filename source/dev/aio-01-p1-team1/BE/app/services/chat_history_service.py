"""로그인 사용자별 진행 중인 AI 상담을 Upstash Redis에 보관합니다."""

from __future__ import annotations

import json
from collections.abc import Callable
from uuid import uuid4

from fastapi import HTTPException, status
from redis.exceptions import WatchError
from app.core.external_error import ExternalServiceError

from app.core.redis_config import (
    get_chat_history_max_messages,
    get_chat_history_ttl,
    get_redis,
)
from app.schemas.chat_schema import ChatHistorySnapshot, ChatMessage

MAX_HISTORY_UPDATE_ATTEMPTS = 3
_UNGUARDED_REVISION = object()


def _history_key(user_id: str) -> str:
    return f"ai-chat:active:{user_id}"


def _storage_error(error: Exception) -> HTTPException:
    return ExternalServiceError(
        service="redis", reason="unavailable",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="현재 대화 기록 저장소에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.",
    )


def _parse_snapshot(raw_history) -> ChatHistorySnapshot:
    if not raw_history:
        return ChatHistorySnapshot()
    rows = json.loads(raw_history) if isinstance(raw_history, (str, bytes)) else raw_history
    # 과거 JSON 목록은 삭제하지 않고 다음 변경 때 revision 형식으로 전환합니다.
    if isinstance(rows, list):
        return ChatHistorySnapshot(messages=rows)
    return ChatHistorySnapshot.model_validate(rows)


def _payload(messages: list[ChatMessage]) -> str:
    return ChatHistorySnapshot(revision=uuid4(), messages=messages).model_dump_json()


def _history_conflict() -> HTTPException:
    return HTTPException(409, "다른 요청에서 상담 기록이 변경되었습니다. 최신 대화를 확인하고 다시 시도해 주세요.")


def _change_history(
    user_id: str,
    change: Callable[[list[ChatMessage]], list[ChatMessage] | None],
    redis_client=None,
    *,
    expected_revision=_UNGUARDED_REVISION,
    preserve_on_conflict: bool = False,
) -> list[ChatMessage]:
    """기록을 읽은 이후 다른 요청이 수정했다면 Redis 저장만 다시 시도합니다."""
    try:
        client = redis_client or get_redis()
        key = _history_key(user_id)
        for _ in range(MAX_HISTORY_UPDATE_ATTEMPTS):
            try:
                with client.pipeline() as pipe:
                    pipe.watch(key)
                    snapshot = _parse_snapshot(pipe.get(key))
                    current = snapshot.messages
                    if expected_revision is not _UNGUARDED_REVISION and snapshot.revision != expected_revision:
                        if preserve_on_conflict:
                            return current
                        raise _history_conflict()
                    updated = change(current)
                    if updated is None:
                        return current
                    selected = updated[-get_chat_history_max_messages():]
                    pipe.multi()
                    # 빈 상태도 revision을 보관해 종료 전 생성한 늦은 답변을 구분합니다.
                    pipe.set(key, _payload(selected), ex=get_chat_history_ttl())
                    pipe.execute()
                    return selected
            except WatchError:
                continue
        raise _history_conflict()
    except HTTPException:
        raise
    except Exception as error:
        raise _storage_error(error) from error


def get_chat_snapshot(user_id: str, redis_client=None) -> ChatHistorySnapshot:
    try:
        client = redis_client or get_redis()
        raw_history = client.get(_history_key(user_id))
        return _parse_snapshot(raw_history)
    except HTTPException:
        raise
    except Exception as error:
        raise _storage_error(error) from error


def get_chat_history(user_id: str, redis_client=None) -> list[ChatMessage]:
    return get_chat_snapshot(user_id, redis_client).messages


def save_chat_history(
    user_id: str,
    messages: list[ChatMessage],
    redis_client=None,
) -> list[ChatMessage]:
    selected = messages[-get_chat_history_max_messages() :]
    payload = _payload(selected)
    try:
        client = redis_client or get_redis()
        client.set(
            _history_key(user_id),
            payload,
            ex=get_chat_history_ttl(),
        )
    except Exception as error:
        raise _storage_error(error) from error
    return selected


def append_chat_exchange(
    user_id: str,
    question: str,
    answer: str,
    redis_client=None,
    *,
    expected_history: list[ChatMessage] | None = None,
    expected_revision=_UNGUARDED_REVISION,
) -> list[ChatMessage]:
    exchange = [ChatMessage(role="user", content=question), ChatMessage(role="assistant", content=answer)]
    def append(current):
        if expected_history is not None and current != expected_history:
            raise _history_conflict()
        return [*current, *exchange]
    return _change_history(user_id, append, redis_client, expected_revision=expected_revision)


def clear_summarized_history(
    user_id: str,
    expected_history: list[ChatMessage],
    redis_client=None,
    *,
    expected_revision=_UNGUARDED_REVISION,
) -> list[ChatMessage]:
    """요약한 기록과 동일할 때만 삭제합니다. 바뀐 기록은 그대로 반환합니다."""
    return _change_history(user_id, lambda current: [] if current == expected_history else None, redis_client, expected_revision=expected_revision, preserve_on_conflict=True)


def delete_chat_history(user_id: str, redis_client=None) -> None:
    try:
        client = redis_client or get_redis()
        client.set(_history_key(user_id), _payload([]), ex=get_chat_history_ttl())
    except Exception as error:
        raise _storage_error(error) from error
