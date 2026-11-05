from datetime import date

def to_date(value: str | None) -> date:
    """API가 돌려준 "2026-08-01" 문자열을 날짜로 바꿉니다."""
    if not value:
        return date.today()
    return date.fromisoformat(value)


