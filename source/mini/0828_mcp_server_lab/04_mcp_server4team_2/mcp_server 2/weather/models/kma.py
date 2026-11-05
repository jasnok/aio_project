from typing import Any


def response_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    response = payload.get("response", payload)
    header = response.get("header", {})
    code = str(header.get("resultCode", "00"))
    if code not in {"0", "00"}:
        raise ValueError(f"기상청 API 오류: {code} {header.get('resultMsg', '')}".strip())
    body = response.get("body", {})
    items = body.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    return items or []
