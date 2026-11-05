"""환경변수 > 앱 .env > 배포 secrets > 기본값. 비밀값을 출력하지 않습니다."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values


class ConfigurationError(RuntimeError):
    """값 대신 설정 이름만 포함하는 사용자용 오류입니다."""


def read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        return {
            name: value or ""
            for name, value in dotenv_values(
                path, encoding="utf-8-sig", interpolate=False
            ).items()
        }
    except (OSError, UnicodeError) as error:
        raise ConfigurationError(f"{path.name} 파일을 UTF-8 형식으로 읽을 수 없습니다.") from error


def is_placeholder(value: str) -> bool:
    return value.startswith(("your-", "https://your-", "YOUR_", "<")) or "your-password@" in value


class Settings:
    def __init__(
        self,
        env_path: Path,
        secret_getter: Callable[[str], object] | None = None,
        environ: Mapping[str, str] | None = None,
    ):
        self.env_path = Path(env_path)
        self.secret_getter = secret_getter
        self.environ = environ

    def file_values(self) -> dict[str, str]:
        return read_env_file(self.env_path)

    def resolve(self, name: str, default: str = "") -> tuple[str, str]:
        environ = os.environ if self.environ is None else self.environ
        value = str(environ.get(name) or "").strip()
        if value:
            return value, "environment"
        value = str(self.file_values().get(name) or "").strip()
        if value:
            return value, ".env"
        if self.secret_getter is not None:
            try:
                value = str(self.secret_getter(name) or "").strip()
            except (FileNotFoundError, KeyError):
                value = ""
            if value:
                return value, "secrets"
        return default, "default"

    def get(self, name: str, default: str = "") -> str:
        return self.resolve(name, default)[0]

    def require(self, name: str) -> str:
        value = self.get(name)
        if not value or is_placeholder(value):
            raise ConfigurationError(
                f"{name} 설정이 없거나 예시 값입니다. "
                f"{self.env_path.parent.name}/.env 또는 배포 secrets를 확인하세요."
            )
        return value

    def http_url(self, name: str, default: str = "") -> str:
        value = self.get(name, default).rstrip("/")
        try:
            parsed = urlsplit(value)
            _ = parsed.port  # 잘못된 포트도 ValueError로 검증합니다.
        except ValueError as error:
            raise ConfigurationError(f"{name} 주소 형식이 올바르지 않습니다.") from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or is_placeholder(value)
            or any(c.isspace() for c in value)
        ):
            raise ConfigurationError(f"{name}에는 http:// 또는 https://로 시작하는 접속 주소를 넣으세요.")
        return value


def read_secrets_files(*paths: Path) -> dict:
    """명령줄 점검용 TOML 로더. 앱 실행 시에는 Streamlit secrets를 사용합니다."""
    import tomllib

    merged = {}
    for path in paths:
        if path.is_file():
            try:
                with path.open("rb") as stream:
                    merged.update(tomllib.load(stream))
            except (OSError, tomllib.TOMLDecodeError) as error:
                raise ConfigurationError("secrets.toml 파일 형식을 확인하세요.") from error
    return merged
