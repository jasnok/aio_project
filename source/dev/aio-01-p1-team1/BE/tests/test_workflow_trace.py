import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi import HTTPException
from app.core import workflow_trace
from app.core.external_error import ExternalServiceError


class WorkflowTraceTests(unittest.TestCase):
    def test_success_records_order_and_one_request_id_with_elapsed_time(self):
        with patch.object(workflow_trace, "add_log") as log:
            with workflow_trace.traced_workflow("chat_answer") as trace:
                with trace.stage("history.read"):
                    pass
        events = [json.loads(call.kwargs["message"]) for call in log.call_args_list]
        self.assertEqual([(event["stage"], event["status"]) for event in events], [("workflow", "started"), ("history.read", "started"), ("history.read", "completed"), ("workflow", "completed")])
        self.assertEqual(len({event["trace_id"] for event in events}), 1)
        self.assertTrue(all(call.kwargs["latency_ms"] >= 0 for call in log.call_args_list))

    def test_error_reason_never_includes_exception_text_or_unknown_reason(self):
        error = ExternalServiceError("gemini", "private-key-value", "private-user-input", 502)
        with patch.object(workflow_trace, "add_log") as log:
            with self.assertRaises(ExternalServiceError):
                with workflow_trace.traced_workflow("chat_summary") as trace:
                    with trace.stage("summary.validate"):
                        raise error
        serialized = " ".join(call.kwargs["message"] for call in log.call_args_list)
        self.assertNotIn("private", serialized)
        failed = [json.loads(call.kwargs["message"]) for call in log.call_args_list if call.kwargs["level"] == "error"]
        self.assertEqual([event["reason"] for event in failed], ["internal", "internal"])
        self.assertEqual(failed[0]["stage"], "summary.validate")

    def test_logging_failure_preserves_original_success_or_conflict(self):
        with patch.object(workflow_trace, "add_log", side_effect=RuntimeError("logger failure")):
            with workflow_trace.traced_workflow("chat_answer"):
                result = "original result"
            self.assertEqual(result, "original result")
            with self.assertRaises(HTTPException) as caught:
                with workflow_trace.traced_workflow("chat_answer"):
                    raise HTTPException(409, "private conflict detail")
            self.assertEqual(caught.exception.status_code, 409)

    def test_concurrent_workflows_have_separate_ids(self):
        barrier = threading.Barrier(2)
        def run():
            with workflow_trace.traced_workflow("chat_answer") as trace:
                with trace.stage("answer.generate"):
                    barrier.wait(timeout=2)
                return trace.trace_id
        with patch.object(workflow_trace, "add_log") as log, ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(lambda _: run(), range(2)))
        self.assertEqual(len(set(ids)), 2)
        events = [json.loads(call.kwargs["message"]) for call in log.call_args_list]
        self.assertEqual({event["trace_id"] for event in events}, set(ids))

    def test_optional_trace_does_not_log_standalone_service_work(self):
        with patch.object(workflow_trace, "add_log") as log:
            with workflow_trace.trace_stage(None, "answer.validate"):
                pass
        log.assert_not_called()

    def test_trace_reaches_existing_log_buffer_without_schema_changes(self):
        from app.core.log_store import get_logs
        with workflow_trace.traced_workflow("chat_answer") as trace:
            with trace.stage("answer.mock"):
                pass
        rows = [row for row in get_logs("all", 200) if trace.trace_id in row["message"]]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(set(row) == {"time", "level", "screen", "message", "latency_ms"} for row in rows))
        self.assertEqual(json.loads(rows[0]["message"])["status"], "completed")
