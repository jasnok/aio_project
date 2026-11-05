"""Execute HTTP requests without a shell."""

import asyncio
import json
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Response:
    output: str
    error: str
    returncode: int


async def request(url: str, method: str, body: str, as_json: bool) -> Response:
    url = url.strip()
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL.")
    if method not in {"GET", "POST", "PUT", "DELETE"}:
        raise ValueError("Unsupported HTTP method.")
    if as_json and body.strip():
        try:
            json.loads(body)
        except ValueError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
    args = [
        "curl", "--disable", "--silent", "--show-error", "--include",
        "--connect-timeout", "10", "--max-time", "60",
        "--proto", "=http,https", "--request", method,
    ]
    if as_json:
        args.extend(["--header", "Content-Type: application/json"])
    if body:
        args.extend(["--data-binary", "@-"])
    args.extend(["--url", url])
    process = await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(body.encode("utf-8") if body else None), timeout=65
        )
    except (asyncio.CancelledError, TimeoutError):
        if process.returncode is None:
            process.kill()
        await process.communicate()
        raise
    return Response(
        stdout.decode("utf-8", errors="replace"),
        stderr.decode("utf-8", errors="replace"),
        process.returncode,
    )
