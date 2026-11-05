# log_store.py
"""실시간 로그를 메모리에 저장하는 buffer입니다.

collections.deque(maxlen=N)에 최근 로그만 들고 있다가 대시보드 폴링에 응답합니다.
서버가 재시작되면 buffer는 사라집니다. 다만 warning/error 로그는 나중에 다시 볼 수 있도록
별도 작업자가 Supabase logs 테이블에도 저장을 시도합니다 (info는 메모리에만 유지).
큐 포화·DB 오류·서버 강제 종료 시 DB 기록은 유실될 수 있는 보조 로그입니다.

로그는 app/main.py의 요청 로깅 미들웨어가 실제 요청을 처리할 때마다 add_log()를
호출해서 쌓입니다 (가짜로 생성하는 시뮬레이터는 쓰지 않습니다).
"""

import threading
import queue
from collections import deque
from datetime import datetime, timezone

from app.core.supabase_config import get_supabase

MAX_LOGS = 200

# DB에 영구 저장할 레벨입니다. info는 양이 많고 다시 볼 필요가 적어 메모리에만 둡니다.
DB_PERSIST_LEVELS = {"warning", "error"}

# 여러 요청이 동시에 buffer를 건드릴 수 있으므로 lock으로 한 번에 하나씩만 접근합니다.
_log_buffer: deque[dict] = deque(maxlen=MAX_LOGS)
_lock = threading.Lock()


class LogWriter:
    """용량 제한 큐를 한 작업자가 처리합니다. 요청 스레드는 DB를 기다리지 않습니다."""

    def __init__(self, save, capacity=200):
        self.save = save
        self.pending = queue.Queue(maxsize=capacity)
        self.stop_event = threading.Event()
        self.thread = None
        self.dropped = 0

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True, name="housing-log-writer")
        self.thread.start()

    def submit(self, entry):
        if not self.thread or not self.thread.is_alive() or self.stop_event.is_set():
            return
        try:
            self.pending.put_nowait(dict(entry))
        except queue.Full:
            self.dropped += 1
            # DB를 재호출하거나 로그를 재귀 생성하지 않습니다.
            print("[log_store] 저장 큐가 가득 차 DB 기록을 생략했습니다.")

    def _run(self):
        while not self.stop_event.is_set() or not self.pending.empty():
            try:
                entry = self.pending.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                self.save(entry)
            except Exception as error:
                print(f"[log_store] 저장 실패 ({type(error).__name__})")
            finally:
                self.pending.task_done()

    def stop(self, timeout=2):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=timeout)


def add_log(level: str, screen: str, message: str, latency_ms: int) -> None:
    """로그를 buffer에 추가합니다. warning/error는 DB 저장 큐에도 넣습니다."""

    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "screen": screen,
        "message": message,
        "latency_ms": latency_ms,
    }
    with _lock:
        _log_buffer.append(entry)

    if level in DB_PERSIST_LEVELS:
        _writer.submit(entry)


def _save_to_db(entry: dict) -> None:
    """warning/error 로그를 Supabase logs 테이블에 저장합니다.

    별도 작업자에서 호출합니다. DB 저장이 실패해도(Supabase 설정 누락,
    네트워크 오류 등) 예외를 밖으로 던지지 않고 무시합니다 — 로그 저장 실패 때문에
    정작 유저의 원래 요청 응답이 실패하면 안 됩니다.
    """

    try:
        get_supabase().table("logs").insert(entry).execute()
    except Exception as error:
        print(f"[log_store] Supabase 저장 실패 ({type(error).__name__})")


_writer = LogWriter(_save_to_db)


def start_log_writer():
    _writer.start()


def stop_log_writer():
    _writer.stop()


def get_logs(level: str | None, limit: int) -> list[dict]:
    """buffer에서 최근 로그를 최신순으로 가져옵니다."""

    with _lock:
        logs = list(_log_buffer)

    if level and level != "all":
        logs = [log for log in logs if log["level"] == level]

    # deque는 오래된 순서로 쌓이므로, 최신 로그가 먼저 오도록 뒤집습니다.
    logs.reverse()
    return logs[:limit]
