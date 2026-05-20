# Research Agent — Design

**Date:** 2026-05-19
**Status:** Approved (pending implementation plan)

## Goal

A small Python CLI that answers a user's question by doing one shallow pass of web research and printing a focused answer to stdout. Built on the Claude Agent SDK using Claude's built-in `WebSearch` and `WebFetch` tools.

## Scope

**In scope**
- Single-file Python script: `research.py`
- One-shot CLI usage: `python research.py "your question"`
- Shallow research loop: one search, a handful of fetches, then summarize
- Streamed text output to stdout

**Out of scope (explicit non-goals)**
- Interactive REPL or multi-turn conversation
- Source citations / URL list / footnotes
- Multi-step planning, gap-analysis, or sub-agents
- Saving reports to disk
- Third-party search providers or MCP servers

## Requirements

- The agent does exactly one research pass per invocation.
- The agent uses only `WebSearch` and `WebFetch`; no other tools.
- The agent's work is bounded by `max_turns=6`.
- The script exits cleanly with non-zero status on user/environment errors.
- The answer streams to stdout as it is produced (no batch-print at the end).
- No source attribution is required in the output unless the user's question explicitly asks for it.

## Architecture

A single Python script in the project root. Async entrypoint drives one `query()` call from `claude-agent-sdk` and prints assistant text as it streams.

```
user shell ──► research.py ──► claude_agent_sdk.query() ──► Claude CLI subprocess
                                                                  │
                                                                  ├─ WebSearch
                                                                  └─ WebFetch
                                ◄──── streamed assistant text ────┘
```

## Components

### 1. CLI entrypoint
- Reads the query as `" ".join(sys.argv[1:])`. This handles both `python research.py "What is X?"` (one quoted arg) and `python research.py What is X?` (multiple args) uniformly.
- Validates that a non-empty query was provided; prints usage and exits 1 otherwise.
- Validates that `ANTHROPIC_API_KEY` is set in the environment; prints a friendly message and exits 1 otherwise.

### 2. Options builder
Constructs a `ClaudeAgentOptions` with:
- `system_prompt`: the shallow-research instructions (see below).
- `allowed_tools=["WebSearch", "WebFetch"]`.
- `max_turns=6`.
- `model`: not set in v1 — let the SDK use its default. An optional `--model` flag may be added later if needed.

### 3. Query runner
- Awaits `query(prompt=<user query>, options=<options>)`.
- Iterates the returned async generator.
- For each `AssistantMessage`, prints the text content of each `TextBlock` to stdout as it arrives (no buffering). Flushes after each print.
- Tool-use and tool-result messages are not printed (we don't want intermediate noise).
- When the stream completes, the script exits 0.

## System prompt

```
You are a fast research assistant. The user will ask a question that requires
brief web research. Do exactly one pass:

1. Use WebSearch once for the question.
2. Use WebFetch on at most 1–3 of the most promising results to read content.
3. Write a concise, direct answer — a few short paragraphs or a tight list.

Constraints:
- Do not run follow-up searches or refine the query — one pass only.
- Do not list URLs or cite sources unless the user explicitly asks.
- Keep the answer focused; do not pad.
```

## Data flow

1. User runs `python research.py "What is X?"`.
2. Script validates args and `ANTHROPIC_API_KEY`.
3. Script builds `ClaudeAgentOptions` and calls `query()`.
4. The SDK spawns the Claude CLI subprocess.
5. Claude calls `WebSearch` once → optionally `WebFetch` on 1–3 results → writes a summary.
6. Assistant text streams to stdout as it is produced.
7. Stream ends → script exits 0.

## Error handling

| Condition | Behavior |
|---|---|
| No query argument provided | Print `Usage: python research.py "your question"`, exit 1 |
| `ANTHROPIC_API_KEY` not set | Print friendly message naming the env var, exit 1 |
| `CLINotFoundError` raised by SDK | Print install hint (`npm install -g @anthropic-ai/claude-code`), exit 1 |
| `ProcessError` or other SDK error | Print the exception message, exit non-zero |
| `max_turns=6` reached without completion | Whatever text streamed has already been printed; exit 0 |

No retries. No silent swallowing of errors.

## Testing

- **Smoke test (manual):** run `python research.py "What is the Claude Agent SDK?"` and verify a coherent multi-paragraph answer streams within ~30 seconds.
- **No automated tests for the agent loop** — output is non-deterministic and requires a live API key.
- **Optional unit tests:** small tests for arg parsing and `ClaudeAgentOptions` construction may be added if desired; not required for v1.

## Dependencies

- Python 3.10+ (for modern async syntax and `claude-agent-sdk` requirements).
- `claude-agent-sdk` (Python package).
- Claude Code CLI installed and on PATH (required by the SDK).
- `ANTHROPIC_API_KEY` in environment.

## File layout

```
SDK-Agent/
├── .claude/
│   └── settings.local.json   (already exists)
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-19-research-agent-design.md  (this file)
├── .venv/                    (virtualenv — installed during setup)
└── research.py               (the script — to be implemented)
```

## Open questions

None at this time. Add a `--model` flag and any further options in a follow-up if needed.
