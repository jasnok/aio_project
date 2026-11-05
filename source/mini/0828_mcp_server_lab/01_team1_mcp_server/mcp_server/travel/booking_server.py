"""8011 포트에서 독립 실행되는 예약(Booking) Streamable HTTP MCP Server입니다."""

import os
import uuid
from datetime import date
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# 0.0.0.0: 이 컴퓨터의 모든 네트워크 인터페이스(loopback 포함)에서 리슨합니다.
# 실제 바인딩/접속 주소는 .env의 MCP_HOST / BOOKING_MCP_URL로 제어하세요. 여기 코드는 건드리지 마세요.
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("BOOKING_MCP_PORT", "8011"))

mcp = FastMCP(
    "mini-agent-booking",
    instructions="호텔 예약을 생성/조회하는 교육용 서버입니다.",
    host=MCP_HOST,
    port=MCP_PORT,
    stateless_http=True,
    json_response=True,
)

# 실습용 메모리 저장소입니다. 실제로는 여기 대신 DB INSERT/SELECT로 교체합니다.
_BOOKINGS: list[dict] = []


@mcp.tool()
def create_booking(
    hotel_id: str,
    guest_name: str,
    checkin_date: str,
    checkout_date: str,
    guest_count: int = 1,
) -> dict:
    """호텔 예약을 생성합니다. 날짜는 YYYY-MM-DD 형식입니다."""
    normalized_hotel_id = hotel_id.strip()
    normalized_guest_name = guest_name.strip()
    if not normalized_hotel_id:
        raise ValueError("hotel_id는 빈 문자열일 수 없습니다.")
    if not normalized_guest_name:
        raise ValueError("guest_name는 빈 문자열일 수 없습니다.")
    if guest_count < 1:
        raise ValueError("guest_count는 1 이상이어야 합니다.")

    try:
        checkin = date.fromisoformat(checkin_date)
        checkout = date.fromisoformat(checkout_date)
    except ValueError as error:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.") from error
    if checkout <= checkin:
        raise ValueError("checkout_date는 checkin_date보다 이후여야 합니다.")

    booking = {
        "booking_id": f"booking-{uuid.uuid4().hex[:8]}",
        "hotel_id": normalized_hotel_id,
        "guest_name": normalized_guest_name,
        "checkin_date": checkin.isoformat(),
        "checkout_date": checkout.isoformat(),
        "guest_count": guest_count,
        "status": "confirmed",
    }

    # TODO: 실제 서비스에서는 아래 print 대신 DB INSERT로 교체합니다.
    print(f"[booking-service] 예약 생성: {booking}")
    _BOOKINGS.append(booking)

    return {
        "booking": booking,
        "source": "booking-service",
    }


@mcp.tool()
def list_bookings(hotel_id: str | None = None) -> dict:
    """지금까지 생성된 예약 목록을 조회합니다. hotel_id를 주면 해당 호텔만 필터링합니다."""
    items = _BOOKINGS
    if hotel_id is not None:
        normalized_hotel_id = hotel_id.strip()
        items = [b for b in _BOOKINGS if b["hotel_id"] == normalized_hotel_id]
    return {
        "items": items,
        "source": "booking-service",
    }


@mcp.tool()
def cancel_booking(booking_id: str) -> dict:
    """booking_id로 예약을 취소합니다."""
    normalized_booking_id = booking_id.strip()
    for booking in _BOOKINGS:
        if booking["booking_id"] == normalized_booking_id:
            booking["status"] = "cancelled"
            print(f"[booking-service] 예약 취소: {normalized_booking_id}")
            return {"booking": booking, "source": "booking-service"}
    raise ValueError(f"booking_id={normalized_booking_id} 예약을 찾을 수 없습니다.")


@mcp.resource("booking://policy/cancellation")
def cancellation_policy() -> str:
    """교육용 예약 취소 정책입니다."""
    return "체크인 24시간 전까지 취소 시 위약금이 없습니다."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
