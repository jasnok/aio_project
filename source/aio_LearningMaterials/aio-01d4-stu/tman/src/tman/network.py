"""Fetch Korean tldr pages from GitHub."""

import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE_URL = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages.ko"


class PageNotFound(Exception):
    """Neither supported directory contains the requested page."""


class NetworkError(Exception):
    """A request failed for a reason other than a missing page."""


class RequestTimeout(NetworkError):
    """A page request timed out."""


def fetch_page(command: str, timeout: float = 10.0) -> str:
    """Try common first, falling back to linux only on HTTP 404."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", command):
        raise ValueError("Use a command name containing letters, digits, _, ., + or -.")
    for platform in ("common", "linux"):
        url = f"{BASE_URL}/{platform}/{command}.md"
        try:
            with urlopen(url, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                continue
            raise NetworkError(f"GitHub returned HTTP {exc.code}.") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise RequestTimeout(f"Request exceeded {timeout:g} seconds.") from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise RequestTimeout(f"Request exceeded {timeout:g} seconds.") from exc
            raise NetworkError(str(exc.reason)) from exc
        except (OSError, UnicodeError) as exc:
            raise NetworkError(str(exc)) from exc
    raise PageNotFound(f"No Korean tldr page for '{command}' in common or linux.")
