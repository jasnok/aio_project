"""Run one app unittest suite with outbound TCP blocked. Run from BE, FE_Admin or FE_User."""

import contextlib
import datetime
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import socket
import sys
import time
import unittest
from unittest.mock import patch
import warnings


sys.path.insert(0, str(Path.cwd()))
suite_name = Path.cwd().name
result_path = Path(__file__).resolve().parents[1] / ".runtime" / f"tests-{suite_name}.json"
result_path.parent.mkdir(parents=True, exist_ok=True)
original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex
original_create = socket.create_connection
blocked_connections = []


def allow_local(address):
    if isinstance(address, tuple) and address[0] not in ("127.0.0.1", "::1", "localhost"):
        blocked_connections.append("blocked")
        raise RuntimeError("External network disabled for baseline test audit")


def guarded_connect(sock, address):
    allow_local(address)
    return original_connect(sock, address)


def guarded_connect_ex(sock, address):
    allow_local(address)
    return original_connect_ex(sock, address)


def guarded_create(address, *args, **kwargs):
    allow_local(address)
    return original_create(address, *args, **kwargs)


captured = io.StringIO()
started = time.perf_counter()
with (
    contextlib.redirect_stdout(captured),
    contextlib.redirect_stderr(captured),
    warnings.catch_warnings(record=True) as warning_records,
    patch.object(socket.socket, "connect", guarded_connect),
    patch.object(socket.socket, "connect_ex", guarded_connect_ex),
    patch.object(socket, "create_connection", guarded_create),
):
    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(stream=captured, verbosity=0).run(suite)

packages = {}
for package in (
    "fastapi", "uvicorn", "pydantic", "python-dotenv", "python-multipart",
    "supabase", "httpx", "streamlit", "pandas", "google-genai", "redis",
    "pypdf", "Pillow", "pydeck", "streamlit-browser-session-storage",
):
    try:
        packages[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        packages[package] = None

summary = {
    "suite": suite_name,
    "recorded_at": datetime.datetime.now().astimezone().isoformat(),
    "python": platform.python_version(),
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skipped": len(result.skipped),
    "successful": result.wasSuccessful(),
    "elapsed_seconds": round(time.perf_counter() - started, 3),
    "external_connections_blocked": len(blocked_connections),
    "failed_test_ids": [test.id() for test, _ in result.failures + result.errors],
    "warning_categories": sorted({item.category.__name__ for item in warning_records}),
    "installed_packages": packages,
    "scope": "App unittest suite; loopback allowed; outbound TCP blocked; no cloud integration validation",
}
result_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
sys.exit(0 if result.wasSuccessful() else 1)
