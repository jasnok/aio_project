"""Plain-text command-line interface."""

import argparse
import sys

from tman.network import NetworkError, PageNotFound, RequestTimeout, fetch_page
from tman.parser import parse_page


def main() -> int:
    parser = argparse.ArgumentParser(description="Show a Korean tldr page.")
    parser.add_argument("command", help="Command to look up, for example tar")
    args = parser.parse_args()
    try:
        page = parse_page(fetch_page(args.command))
    except PageNotFound as exc:
        print(f"Page not found: {exc}", file=sys.stderr)
        return 1
    except RequestTimeout as exc:
        print(f"Timeout: {exc}", file=sys.stderr)
        return 3
    except NetworkError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        parser.error(str(exc))
    print(page.title)
    if page.description:
        print(f"\n{page.description}")
    for example in page.examples:
        print(f"\n- {example.description}\n  {example.command}")
    return 0
