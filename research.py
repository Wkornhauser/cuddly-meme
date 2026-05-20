"""research.py — one-shot web research CLI built on the Claude Agent SDK.

Usage:
    python research.py "your question here"
"""

from __future__ import annotations

import sys
from typing import Mapping


def parse_query(argv: list[str]) -> str:
    """Join argv[1:] into a single query string.

    Prints usage to stderr and exits 1 if the resulting string is empty
    or whitespace-only.
    """
    query = " ".join(argv[1:]).strip()
    if not query:
        print('Usage: python research.py "your question"', file=sys.stderr)
        raise SystemExit(1)
    return query


def check_api_key(env: Mapping[str, str]) -> None:
    """Verify ANTHROPIC_API_KEY is present and non-empty.

    Prints a friendly message to stderr and exits 1 otherwise.
    """
    if not env.get("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY is not set. Export it in your environment "
            "before running this script.",
            file=sys.stderr,
        )
        raise SystemExit(1)
