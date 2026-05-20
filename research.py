"""research.py — one-shot web research CLI built on the Claude Agent SDK.

Usage:
    python research.py "your question here"
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Mapping

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    CLINotFoundError,
    ProcessError,
    TextBlock,
    query,
)


def parse_query(argv: list[str]) -> str:
    """Join argv[1:] into a single query string.

    Prints usage to stderr and exits 1 if the resulting string is empty
    or whitespace-only.
    """
    text = " ".join(argv[1:]).strip()
    if not text:
        print('Usage: python research.py "your question"', file=sys.stderr)
        raise SystemExit(1)
    return text


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


SYSTEM_PROMPT = (
    "You are a fast research assistant. The user will ask a question that "
    "requires brief web research. Do exactly one pass:\n"
    "1. Use WebSearch once for the question.\n"
    "2. Use WebFetch on at most 1-3 of the most promising results to read "
    "their content.\n"
    "3. Write a concise, direct answer - a few short paragraphs or a tight "
    "list.\n\n"
    "Constraints:\n"
    "- Do not run follow-up searches or refine the query - one pass only.\n"
    "- Do not list URLs or cite sources unless the user explicitly asks.\n"
    "- Keep the answer focused; do not pad.\n"
    "- Only use the WebSearch and WebFetch tools."
)


def build_options() -> ClaudeAgentOptions:
    """Construct the ClaudeAgentOptions used for every research run."""
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["WebSearch", "WebFetch"],
        max_turns=6,
    )


async def run_query(prompt: str, options: ClaudeAgentOptions) -> None:
    """Run a single shallow research pass and stream assistant text to stdout.

    Prints only TextBlock content from AssistantMessage messages; tool-use
    and tool-result messages are deliberately skipped to keep stdout clean.
    """
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
        # Final newline so the shell prompt lands on its own line.
        print()
    except CLINotFoundError:
        print(
            "Claude Code CLI not found on PATH. Install with:\n"
            "  npm install -g @anthropic-ai/claude-code",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except ProcessError as exc:
        print(f"Claude CLI process error: {exc}", file=sys.stderr)
        raise SystemExit(2)


async def main() -> None:
    """Orchestrate one research run end-to-end."""
    prompt = parse_query(sys.argv)
    check_api_key(os.environ)
    options = build_options()
    await run_query(prompt, options)


if __name__ == "__main__":
    # Windows consoles default to cp1252 and crash on common Unicode (e.g. →, em-dashes).
    # Reconfigure stdio to UTF-8 so streamed output survives intact.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    asyncio.run(main())
