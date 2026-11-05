"""Supabase/PostgreSQL 예외를 안전하게 분류하는 도구입니다."""


def is_unique_violation(error: Exception) -> bool:
    """PostgreSQL unique violation 코드 23505인지 확인합니다."""

    code = getattr(error, "code", None)
    if code == "23505":
        return True
    return "23505" in str(error)
