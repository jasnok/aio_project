"""Render a JSON response body as YAML without changing the original response."""

import json
import re

import yaml


def response_yaml(output: str) -> str:
    body = output
    # curl --include may emit multiple header blocks (proxy CONNECT or HTTP 100).
    while body.startswith("HTTP/"):
        separator = re.search(r"\r?\n\r?\n", body)
        if separator is None:
            return "YAML unavailable: response body is not valid JSON."
        body = body[separator.end():]
    try:
        value = json.loads(body)
    except ValueError:
        return "YAML unavailable: response body is not valid JSON."
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False)
