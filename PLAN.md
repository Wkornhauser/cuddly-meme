# Research Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-shot Python CLI (`research.py`) that takes a question, performs one shallow pass of web research via the Claude Agent SDK's built-in `WebSearch` + `WebFetch` tools, and streams a focused answer to stdout.

**Architecture:** Single Python script. Async `main()` parses argv, validates env, builds `ClaudeAgentOptions`, calls `claude_agent_sdk.query(...)`, and iterates the async stream printing `TextBlock` text as it arrives. No persistent state, no source citations, no follow-up loops.

**Tech Stack:** Python 3.10+, `claude-agent-sdk`, Claude Code CLI (already on PATH for the SDK subprocess), `pytest` for the small unit-test suite.

**Spec:** `docs/superpowers/specs/2026-05-19-research-agent-design.md`

---

## File Structure

```
SDK-Agent/
├── research.py                 (NEW — the CLI script)
├── tests/
│   ├── __init__.py             (NEW — empty, makes tests a package)
│   └── test_research.py        (NEW — unit tests for pure helpers)
├── .venv/                      (NEW — virtualenv)
├── docs/
│   └── superpowers/
│       ├── specs/2026-05-19-research-agent-design.md   (exists)
│       └── plans/2026-05-19-research-agent.md          (this file)
└── .claude/settings.local.json (exists)
```

**Module layout for `research.py`:**

- `parse_query(argv: list[str]) -> str` — joins `argv[1:]`; on empty input, prints usage to stderr and `sys.exit(1)`.
- `check_api_key(env: Mapping[str, str]) -> None` — raises `SystemExit(1)` with a friendly stderr message if `ANTHROPIC_API_KEY` is missing.
- `build_options() -> ClaudeAgentOptions` — returns the options object (system prompt, allowed_tools, max_turns).
- `run_query(prompt: str, options: ClaudeAgentOptions) -> None` (async) — iterates `query(...)`, prints `TextBlock` text from each `AssistantMessage` to stdout, flushing after each print.
- `main() -> None` (async) — orchestrates the four helpers above.
- `if __name__ == "__main__": asyncio.run(main())` at the bottom.

Helpers are deliberately broken out so we can unit-test the deterministic ones (`parse_query`, `check_api_key`, `build_options`) without invoking the SDK.

---

## Conventions

- **Shell:** Use the `Bash` tool for these commands (the project's `.claude/settings.local.json` pre-approves the Bash forms below). All paths assume the working directory is `C:\Users\Wil\Desktop\SDK-Agent`.
- **Python invocation:** `.venv/Scripts/python.exe` (Windows venv layout).
- **Tests:** `pytest`, with tests under `tests/`.
- **No git commits in this plan.** The project is not currently a git repository. If the user later runs `git init`, the implementer should add a commit at the end of each task using a conventional commit message (one suggestion is included in each task — skip it until a repo exists).

---

## Task 1: Set up the virtualenv and install dependencies

**Files:**
- Create: `.venv/` (via `python -m venv`)
- No source files yet

- [ ] **Step 1: Confirm Python is available**

Run: `where python`
Expected: at least one path to a `python.exe` (e.g., `C:\Python311\python.exe`). If nothing prints, install Python 3.10+ before continuing.

- [ ] **Step 2: Create the virtualenv**

Run: `python -m venv .venv`
Expected: silent success; the directory `.venv/` is created with `Scripts/python.exe` inside.

- [ ] **Step 3: Upgrade pip in the venv (quiet)**

Run: `.venv/Scripts/python.exe -m pip install --upgrade pip --quiet`
Expected: returns exit 0 with no output.

- [ ] **Step 4: Install `claude-agent-sdk`**

Run: `.venv/Scripts/python.exe -m pip install claude-agent-sdk --quiet`
Expected: exit 0.

- [ ] **Step 5: Install `pytest` (for the small test suite)**

Run: `.venv/Scripts/python.exe -m pip install pytest --quiet`
Expected: exit 0. (Note: this command is **not** in the pre-approved allowlist in `.claude/settings.local.json`; the implementer will need to approve it once or add it to the allowlist.)

- [ ] **Step 6: Verify the SDK is importable**

Run: `.venv/Scripts/python.exe -m pip show claude-agent-sdk`
Expected: output begins with `Name: claude-agent-sdk` and shows a Version line.

- [ ] **Step 7: Verify the Claude Code CLI is on PATH**

Run: `claude --version`
Expected: prints a version string. If "command not found", install via `npm install -g @anthropic-ai/claude-code` before continuing — the SDK shells out to this CLI.

- [ ] **Step 8: Verify `ANTHROPIC_API_KEY` is set in the shell**

Run (PowerShell, if using the PowerShell tool): `if ($env:ANTHROPIC_API_KEY) { 'OK' } else { 'MISSING' }`
Or (Bash): `[ -n "$ANTHROPIC_API_KEY" ] && echo OK || echo MISSING`
Expected: `OK`. If `MISSING`, set the env var before the smoke test in Task 6. (The script's runtime check will catch this anyway — this is just a setup sanity check.)

- [ ] **Step 9: Commit (skip if no git repo)**

If `.git/` exists:
```bash
git add .venv/.gitignore || true
git commit -m "chore: set up venv and install claude-agent-sdk + pytest"
```
Otherwise: skip.

---

## Task 2: Add `parse_query` and `check_api_key` with tests (TDD)

**Files:**
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_research.py`
- Create: `research.py`

- [ ] **Step 1: Create the empty test package marker**

Create `tests/__init__.py` as an empty file (zero bytes). This lets `pytest` discover the `tests` package cleanly on Windows.

- [ ] **Step 2: Write the failing tests for `parse_query` and `check_api_key`**

Create `tests/test_research.py` with this exact content:

```python
import pytest

from research import parse_query, check_api_key


class TestParseQuery:
    def test_joins_multiple_argv_into_one_string(self):
        assert parse_query(["research.py", "What", "is", "X?"]) == "What is X?"

    def test_returns_single_quoted_argument_unchanged(self):
        assert parse_query(["research.py", "What is X?"]) == "What is X?"

    def test_exits_when_no_query_provided(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_query(["research.py"])
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Usage" in captured.err

    def test_exits_when_query_is_only_whitespace(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_query(["research.py", "   "])
        assert excinfo.value.code == 1


class TestCheckApiKey:
    def test_passes_when_key_is_set(self):
        check_api_key({"ANTHROPIC_API_KEY": "sk-test-value"})  # should not raise

    def test_exits_when_key_is_missing(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            check_api_key({})
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY" in captured.err

    def test_exits_when_key_is_empty_string(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            check_api_key({"ANTHROPIC_API_KEY": ""})
        assert excinfo.value.code == 1
```

- [ ] **Step 3: Run the tests and confirm they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_research.py -v`
Expected: collection error or `ModuleNotFoundError: No module named 'research'` — because `research.py` does not exist yet. This is the failing state we want.

- [ ] **Step 4: Create `research.py` with the minimum to pass the tests**

Create `research.py` with this exact content:

```python
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
```

- [ ] **Step 5: Run the tests and confirm they all pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_research.py -v`
Expected: 6 tests pass (4 `TestParseQuery` + 3 `TestCheckApiKey` — wait, that's 7). Recount: `joins_multiple`, `returns_single`, `exits_when_no_query`, `exits_when_whitespace` = 4 in `TestParseQuery`; `passes_when_set`, `exits_when_missing`, `exits_when_empty` = 3 in `TestCheckApiKey`. **7 tests, all passing.**

- [ ] **Step 6: Commit (skip if no git repo)**

If `.git/` exists:
```bash
git add research.py tests/__init__.py tests/test_research.py
git commit -m "feat: add parse_query and check_api_key with unit tests"
```
Otherwise: skip.

---

## Task 3: Add `build_options()` with a test

**Files:**
- Modify: `research.py` (append `build_options`)
- Modify: `tests/test_research.py` (append a new test class)

- [ ] **Step 1: Write the failing test for `build_options`**

Append the following to `tests/test_research.py` (after the existing `TestCheckApiKey` class):

```python
from research import build_options


class TestBuildOptions:
    def test_returns_options_with_websearch_and_webfetch_allowed(self):
        opts = build_options()
        assert "WebSearch" in opts.allowed_tools
        assert "WebFetch" in opts.allowed_tools

    def test_caps_max_turns_at_six(self):
        opts = build_options()
        assert opts.max_turns == 6

    def test_system_prompt_mentions_one_pass(self):
        opts = build_options()
        # The system prompt should constrain Claude to a single research pass.
        assert opts.system_prompt is not None
        text = opts.system_prompt.lower()
        assert "one pass" in text or "one round" in text or "exactly one" in text
```

- [ ] **Step 2: Run the new tests and confirm they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_research.py::TestBuildOptions -v`
Expected: `ImportError: cannot import name 'build_options' from 'research'`.

- [ ] **Step 3: Add `build_options` and the SDK import to `research.py`**

At the top of `research.py`, replace the existing import block with:

```python
from __future__ import annotations

import sys
from typing import Mapping

from claude_agent_sdk import ClaudeAgentOptions
```

Then append this function to the bottom of `research.py` (after `check_api_key`):

```python
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
```

- [ ] **Step 4: Run all tests and confirm they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_research.py -v`
Expected: 10 tests pass (7 from Task 2 + 3 new).

- [ ] **Step 5: Commit (skip if no git repo)**

```bash
git add research.py tests/test_research.py
git commit -m "feat: add build_options with allowed_tools and shallow system prompt"
```

---

## Task 4: Add the async `run_query` streaming function

**Files:**
- Modify: `research.py`

No automated test — the SDK call requires a live API key and produces non-deterministic output. Manual smoke test in Task 6 covers it.

- [ ] **Step 1: Extend the SDK import**

At the top of `research.py`, replace the SDK import line:

```python
from claude_agent_sdk import ClaudeAgentOptions
```

with:

```python
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    CLINotFoundError,
    ProcessError,
    TextBlock,
    query,
)
```

- [ ] **Step 2: Append the `run_query` function**

Append to the bottom of `research.py`:

```python
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
```

- [ ] **Step 3: Run existing tests to confirm nothing regressed**

Run: `.venv/Scripts/python.exe -m pytest tests/test_research.py -v`
Expected: 10 tests still pass.

- [ ] **Step 4: Commit (skip if no git repo)**

```bash
git add research.py
git commit -m "feat: add run_query with streaming output and SDK error handling"
```

---

## Task 5: Wire `main()` and the `__main__` entry point

**Files:**
- Modify: `research.py`

- [ ] **Step 1: Add `asyncio` and `os` to the top-of-file imports**

In `research.py`, replace the existing import block:

```python
from __future__ import annotations

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
```

with:

```python
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
```

- [ ] **Step 2: Append `main()` and the `__main__` entry block**

Append to the bottom of `research.py`:

```python
async def main() -> None:
    """Orchestrate one research run end-to-end."""
    prompt = parse_query(sys.argv)
    check_api_key(os.environ)
    options = build_options()
    await run_query(prompt, options)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 3: Verify the script at least starts (no SDK call yet)**

Run: `.venv/Scripts/python.exe research.py`
Expected: prints `Usage: python research.py "your question"` to stderr and exits 1.

- [ ] **Step 4: Verify the missing-API-key path**

Run (Bash): `ANTHROPIC_API_KEY="" .venv/Scripts/python.exe research.py "test"`
Or (PowerShell): `$env:ANTHROPIC_API_KEY=""; .venv/Scripts/python.exe research.py "test"`
Expected: prints the `ANTHROPIC_API_KEY is not set` message to stderr and exits 1.
(Remember to restore your real `ANTHROPIC_API_KEY` afterward in PowerShell.)

- [ ] **Step 5: Run the full test suite one more time**

Run: `.venv/Scripts/python.exe -m pytest tests/test_research.py -v`
Expected: 10 tests pass.

- [ ] **Step 6: Commit (skip if no git repo)**

```bash
git add research.py
git commit -m "feat: wire main() and __main__ entry"
```

---

## Task 6: End-to-end smoke test

**Files:** none modified.

- [ ] **Step 1: Confirm `ANTHROPIC_API_KEY` is set**

Run (Bash): `[ -n "$ANTHROPIC_API_KEY" ] && echo OK || echo MISSING`
Or (PowerShell): `if ($env:ANTHROPIC_API_KEY) { 'OK' } else { 'MISSING' }`
Expected: `OK`.

- [ ] **Step 2: Run the agent against a simple, current-events-light query**

Run: `.venv/Scripts/python.exe research.py "What is the Claude Agent SDK?"`

Expected (within ~30–60 seconds):
- Text streams to stdout incrementally (not all at once at the end).
- The final output is a coherent multi-paragraph answer describing the Claude Agent SDK.
- The script exits 0.
- No source-list / no URLs (the system prompt forbids them).

If the output appears in a single burst at the end rather than streaming, the script still works — but check that `flush=True` is present on the `print(block.text, end="", flush=True)` line in `run_query`.

- [ ] **Step 3: Run the agent against a second query to confirm behavior is consistent**

Run: `.venv/Scripts/python.exe research.py "What are the main differences between async/await and threading in Python?"`

Expected: another coherent answer, similar latency, exit 0.

- [ ] **Step 4: Sanity-check failure modes**

(a) Missing argument:
Run: `.venv/Scripts/python.exe research.py`
Expected: prints usage to stderr, exits 1.

(b) Bogus API key (optional — only if you're comfortable temporarily overriding):
Run (Bash): `ANTHROPIC_API_KEY="sk-invalid" .venv/Scripts/python.exe research.py "test"`
Expected: a `Claude CLI process error: ...` message on stderr and a non-zero exit. (Exact wording varies with the CLI version.) Restore your real key afterward.

- [ ] **Step 5: Done.**

If all of the above worked, the agent is complete. There are no further tasks. If anything failed, capture the exact command and stderr and bring it back for diagnosis.

---

## Spec Coverage Self-Review (do not skip)

Cross-check the spec against this plan before declaring it complete.

| Spec requirement | Implementing task |
|---|---|
| Single Python script `research.py` | Tasks 2–5 |
| One-shot CLI usage | Task 5 (`__main__` block) |
| Shallow research loop (one pass) | Task 3 (system prompt) + Task 3 (`max_turns=6`) |
| `WebSearch` + `WebFetch` only | Task 3 (`allowed_tools`) + Task 3 (system prompt) |
| `max_turns=6` | Task 3 |
| Streamed text output to stdout | Task 4 (`print(..., flush=True)`) |
| Missing query arg → exit 1 | Task 2 (`parse_query`) |
| Missing `ANTHROPIC_API_KEY` → exit 1 | Task 2 (`check_api_key`) |
| `CLINotFoundError` → install hint, exit 1 | Task 4 (`run_query`) |
| `ProcessError` → message, exit non-zero | Task 4 (`run_query`) |
| `max_turns` reached without final answer → exit 0 with partial text | Task 4 (no special handling needed; the stream just ends) |
| No source/URL citations in output | Task 3 (system prompt) |
| Optional unit tests for arg parsing and options | Tasks 2 and 3 |
| Smoke test | Task 6 |

All spec requirements are covered by at least one task.
