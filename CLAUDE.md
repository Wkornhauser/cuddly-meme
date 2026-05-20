# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# Behavioral guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" becomes "Write tests for invalid inputs, then make them pass"
- "Fix the bug" becomes "Write a test that reproduces it, then make it pass"
- "Refactor X" becomes "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
- Step 1 and what to verify
- Step 2 and what to verify
- Step 3 and what to verify

Strong success criteria let you loop independently. Weak criteria require constant clarification.

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# Project-specific guidance

## Project overview

This repository implements a small one-shot Python CLI ("research agent") built on the [`claude-agent-sdk`](https://pypi.org/project/claude-agent-sdk/). The agent takes a question on the command line, performs one shallow pass of web research using Claude's built-in `WebSearch` and `WebFetch` tools, and streams a focused answer to stdout.

**Authoritative sources:**
- Spec: `SPECS.md` (canonical copy: `docs/superpowers/specs/2026-05-19-research-agent-design.md`)
- Plan: `PLAN.md` (canonical copy: `docs/superpowers/plans/2026-05-19-research-agent.md`)

At the time of writing, the source file (`research.py`) has not been implemented yet — the design and plan are authoritative until the code exists. This project is **not** currently a git repository; the plan's per-task commit steps should be skipped until `git init` is run.

**Requires:** Python 3.10+, the Claude Code CLI on PATH, and `ANTHROPIC_API_KEY` in the environment.

## Common commands

All commands assume the working directory is the project root (`C:\Users\Wil\Desktop\SDK-Agent`) and use the local virtualenv's Python on Windows.

```bash
# One-time setup
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip --quiet
.venv/Scripts/python.exe -m pip install claude-agent-sdk pytest --quiet

# Run the agent (requires ANTHROPIC_API_KEY in env, plus the Claude CLI on PATH)
.venv/Scripts/python.exe research.py "your question here"

# Run the full test suite
.venv/Scripts/python.exe -m pytest tests/ -v

# Run a single test class or test
.venv/Scripts/python.exe -m pytest tests/test_research.py::TestParseQuery -v
.venv/Scripts/python.exe -m pytest tests/test_research.py::TestBuildOptions::test_caps_max_turns_at_six -v
```

The Claude Code CLI must be installed and on PATH (`npm install -g @anthropic-ai/claude-code`) — the `claude-agent-sdk` shells out to it.

## Architecture

The agent is intentionally a single Python script, not a package. The module layout for `research.py`:

- `parse_query(argv) -> str` — joins `sys.argv[1:]`; on empty/whitespace input prints usage to stderr and `sys.exit(1)`.
- `check_api_key(env) -> None` — exits 1 with a friendly stderr message if `ANTHROPIC_API_KEY` is missing.
- `build_options() -> ClaudeAgentOptions` — returns the options object with the shallow-research system prompt, `allowed_tools=["WebSearch", "WebFetch"]`, and `max_turns=6`. Does not set `model` — the SDK's default is used.
- `run_query(prompt, options)` (async) — iterates `claude_agent_sdk.query(...)`, prints `TextBlock` content from each `AssistantMessage` as it streams (flushed). Tool-use / tool-result messages are deliberately not printed. Catches `CLINotFoundError` and `ProcessError` from the SDK and exits with a friendly message.
- `main()` (async) — orchestrates the four helpers in order: parse → check env → build options → run query.
- `if __name__ == "__main__": asyncio.run(main())` at the bottom.

The deterministic helpers (`parse_query`, `check_api_key`, `build_options`) are unit-tested under `tests/`. The async `run_query` and the end-to-end flow are covered only by a manual smoke test (non-deterministic, requires a live API key).

## Key design constraints

These come from the spec and should not be relaxed without updating `SPECS.md` first:

- **Shallow loop only.** One `WebSearch`, 1–3 `WebFetch` calls, then a final summary. No iterative refinement, no sub-agents, no follow-up searches.
- **No source citations.** The system prompt explicitly tells Claude not to list URLs or footnotes unless the user's question asks for them.
- **One-shot CLI, no REPL.** Each invocation handles a single query and exits.
- **Tools restricted to `WebSearch` + `WebFetch`** via `allowed_tools`. No Bash, no Read/Write/Edit, no third-party search APIs, no MCP servers.
- **`max_turns=6`** caps the agent loop.
- **Streamed output.** Assistant text must reach stdout incrementally (with `flush=True`), not as a single batch at the end.

## Explicit non-goals

The spec calls these out as out-of-scope. Don't add them without revising the spec:

- Interactive REPL or multi-turn conversation
- Source citations, URL list, or footnotes
- Multi-step planning, gap analysis, or sub-agents
- Saving reports to disk
- Third-party search providers (Tavily, Brave, Exa) or MCP servers

## Error handling contract

| Condition | Behavior |
|---|---|
| No query argument | `Usage: ...` to stderr, exit 1 |
| `ANTHROPIC_API_KEY` missing/empty | friendly message to stderr, exit 1 |
| `CLINotFoundError` from SDK | install hint to stderr, exit 1 |
| `ProcessError` or other SDK error | message to stderr, exit non-zero |
| `max_turns=6` reached without a final answer | whatever streamed has already been printed; exit 0 |

No retries. No silent swallowing.

## Pre-approved tooling

`.claude/settings.local.json` pre-approves a small allowlist of bash commands for the venv setup (`python -m venv .venv`, the two `pip install` commands for `claude-agent-sdk` and the pip upgrade, and `pip show claude-agent-sdk`). Other commands — including `pip install pytest` — will prompt the first time and may be added to the allowlist if desired.
