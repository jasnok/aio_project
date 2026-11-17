"""PostgreSQL 연결과 공통 조회 함수입니다."""

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from ..core.config import settings
from ..core.errors import ConfigurationError


def database_url() -> str:
    if not settings.database_url:
        raise ConfigurationError("DATABASE_URL 환경변수가 필요합니다.")
    return settings.database_url


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(
        database_url(), connect_timeout=5, row_factory=dict_row
    ) as connection:
        yield connection


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict | None:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
