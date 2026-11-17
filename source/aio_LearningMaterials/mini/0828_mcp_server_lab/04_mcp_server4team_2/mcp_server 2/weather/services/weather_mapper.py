from typing import Any


def to_number(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number >= 900 or number <= -900 else number


def map_kma_items(items: list[dict]) -> dict[tuple[str, str], dict[str, Any]]:
    mapped = {}
    for item in items:
        date = str(item.get("fcstDate", item.get("baseDate", "")))
        time = str(item.get("fcstTime", item.get("baseTime", "")))
        category = item.get("category")
        value = item.get("fcstValue", item.get("obsrValue"))
        mapped.setdefault((date, time), {})[category] = to_number(value) if category not in {"PTY", "SKY"} else value
    return mapped
