"""관광지 검색 과정에서 사용하는 예외입니다."""


class TourApiError(RuntimeError):
    """TourAPI 호출 또는 응답 처리에 실패했을 때 발생합니다."""


class AmbiguousLocationError(ValueError):
    """같은 이름의 국내 지역이 둘 이상 발견됐을 때 발생합니다."""
