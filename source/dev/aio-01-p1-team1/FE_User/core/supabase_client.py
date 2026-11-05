"""Supabase Auth 연결. 사용자 화면에는 anon/publishable key만 사용합니다."""

from supabase import Client, create_client

from core.settings import settings


def get_required_env(name: str) -> str:
    return settings.require(name)


def get_supabase() -> Client:
    url = settings.http_url("SUPABASE_URL")
    anon_key = get_required_env("SUPABASE_ANON_KEY")
    return create_client(url, anon_key)
