"""기존 관리자 로그에 상담 단계만 남깁니다. 입력·출력·사용자 ID는 받지 않습니다."""
import json
from contextlib import contextmanager, nullcontext
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException
from app.core.log_store import add_log

SAFE_REASONS = {"timeout", "configuration", "rate_limit", "invalid_response", "unavailable", "busy"}


def failure_reason(error: Exception) -> str:
    reason = getattr(error, "reason", None)
    if isinstance(reason, str) and reason in SAFE_REASONS:
        return reason
    if isinstance(error, HTTPException) and error.status_code == 409:
        return "conflict"
    return "internal"


class WorkflowTrace:
    def __init__(self, workflow: str):
        self.workflow = workflow
        self.trace_id = str(uuid4())

    def emit(self, stage: str, status: str, elapsed_ms: int = 0, reason: str | None = None):
        event = {"trace_id": self.trace_id, "workflow": self.workflow, "stage": stage, "status": status}
        if reason:
            event["reason"] = reason
        try:
            add_log(level="error" if status == "failed" else "info",
                    screen=f"AI:{self.workflow}", message=json.dumps(event, ensure_ascii=False),
                    latency_ms=elapsed_ms)
        except Exception:
            # 보조 로그의 장애가 원래 성공 응답·예외를 바꾸지 않도록 합니다.
            pass

    @contextmanager
    def stage(self, name: str):
        started = perf_counter()
        self.emit(name, "started")
        try:
            yield
        except Exception as error:
            self.emit(name, "failed", int((perf_counter() - started) * 1000), failure_reason(error))
            raise
        else:
            self.emit(name, "completed", int((perf_counter() - started) * 1000))


@contextmanager
def traced_workflow(name: str):
    trace = WorkflowTrace(name)
    with trace.stage("workflow"):
        yield trace


def trace_stage(trace: WorkflowTrace | None, name: str):
    return trace.stage(name) if trace else nullcontext()
