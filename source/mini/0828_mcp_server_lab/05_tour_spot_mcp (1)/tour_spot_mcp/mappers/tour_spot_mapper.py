"""TourAPI 원본 응답을 관광지 Schema로 변환합니다."""

from typing import Any

from schemas.tour_spot import TourSpot


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_items(body: dict[str, Any]) -> list[dict[str, Any]]:
    """TourAPI body에서 객체 목록만 안전하게 꺼냅니다."""
    items_container = body.get("items")
    if not isinstance(items_container, dict):
        return []
    items = items_container.get("item", [])
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    return []


def map_tour_spots(body: dict[str, Any]) -> list[TourSpot]:
    """TourAPI 관광지 목록을 내부 TourSpot 목록으로 변환합니다."""
    return [
        TourSpot(
            content_id=str(item.get("contentid", "")),
            name=str(item.get("title", "")).strip(),
            address=_optional_text(item.get("addr1")),
            image_url=_optional_text(item.get("firstimage")),
            latitude=_optional_float(item.get("mapy")),
            longitude=_optional_float(item.get("mapx")),
        )
        for item in extract_items(body)
        if item.get("contentid") and item.get("title")
    ]
