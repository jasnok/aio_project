from datetime import date

import pytest

from mcp_server.tools import facility_tools, product_tools


def test_product_search_rejects_blank_term():
    with pytest.raises(ValueError, match="1~100"):
        product_tools.find_products(" ")


def test_facility_session_range_is_limited_to_90_days():
    with pytest.raises(ValueError, match="0~90"):
        facility_tools.get_program_sessions(
            "PG-YOGA", date(2026, 1, 1), date(2026, 4, 2)
        )


def test_inventory_preserves_zero_quantity(monkeypatch):
    monkeypatch.setattr(
        product_tools.db,
        "availability",
        lambda product_id: [{"product_id": product_id, "quantity": 0}],
    )
    result = product_tools.get_product_availability("AC-A30")
    assert result["items"][0]["quantity"] == 0
