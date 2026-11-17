"""Tour Spot MCP 예외 패키지입니다."""

from .tour_api import AmbiguousLocationError, TourApiError

__all__ = ["AmbiguousLocationError", "TourApiError"]
