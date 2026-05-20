# research-agent

A one-shot Python CLI that answers a question with a single shallow pass of web research, built on the [Claude Agent SDK](https://pypi.org/project/claude-agent-sdk/).

## What It Does

You give it a question on the command line. It runs one round of web research using Claude's built-in `WebSearch` and `WebFetch` tools and streams a focused answer back to your terminal. There is no conversation, no source list, and no follow-up loop — just one query in, one answer out.

## Architecture

A single Python script, `research.py`, drives the whole thing:

- **`parse_query` / `check_api_key`** — argv parsing and `ANTHROPIC_API_KEY` validation. Either failure prints a friendly message to stderr and exits 1.
- **`build_options`** — constructs the `ClaudeAgentOptions` with the shallow-research system prompt, `allowed_tools=["WebSearch", "WebFetch"]`, and `max_turns=6`.
- **`run_query`** — async function that iterates `claude_agent_sdk.query(...)` and streams `TextBlock` content from each `AssistantMessage` straight to stdout (flushed). Catches `CLINotFoundError` and `ProcessError` from the SDK with distinct exit codes.
- **`main` / `__main__`** — orchestrates the four helpers and reconfigures stdout/stderr to UTF-8 so streamed output survives on Windows (`cp1252` consoles otherwise crash on common Unicode like `→` and em-dashes).

The SDK shells out to the Claude Code CLI under the hood, which is why the CLI must be on `PATH`.

## Setup

### Prerequisites

- Python 3.10 or newer
- [Claude Code CLI](https://docs.claude.com/en/docs/claude-code) on `PATH` (`npm install -g @anthropic-ai/claude-code`)
- An Anthropic API key

### Installation

```bash
# From the project root
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install claude-agent-sdk pytest
```

(On macOS/Linux replace `.venv/Scripts/python.exe` with `.venv/bin/python`.)

### Environment

Copy `.env.example` to `.env` and set your real API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

`research.py` reads `ANTHROPIC_API_KEY` from `os.environ`. It does not auto-load `.env` — export the variable in your shell before running, e.g.:

```bash
set -a; source .env; set +a
```

### Run it

```bash
.venv/Scripts/python.exe research.py "your question here"
```

### Run the tests

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

## Usage

**Example 1 — a quick research question:**

```
$ python research.py "What is the capital of Iceland and what's it known for?"
The capital of Iceland is Reykjavík, located on the country's southwestern
coast. At 64°N latitude, it's the world's northernmost capital of a sovereign
state, and it's home to roughly two-thirds of Iceland's population in its
greater metropolitan area.

Reykjavík is best known for:
- Geothermal living — the city is heated almost entirely by hot water piped
  from nearby geothermal springs...
- Clean, safe, and green — consistently ranked among the world's cleanest
  and safest capitals...
- Gateway to Iceland's nature — it's the launching point for the Golden
  Circle, the Northern Lights, glaciers, volcanoes, and whale watching.
...
```

**Example 2 — missing the query argument:**

```
$ python research.py
Usage: python research.py "your question"
$ echo $?
1
```

## Project Structure

```
SDK-Agent/
├── research.py              The CLI script — the entire agent lives here
├── tests/
│   ├── __init__.py          Empty marker so pytest discovers the package
│   └── test_research.py     10 unit tests covering the deterministic helpers
├── SPECS.md                 The design spec (authoritative for behavior)
├── PLAN.md                  The original task-by-task implementation plan
├── CLAUDE.md                Guidance for Claude Code working in this repo
├── .env.example             Template for the required ANTHROPIC_API_KEY
├── .gitignore               Excludes .env, .venv, caches, etc.
└── docs/superpowers/        Canonical copies of the spec and plan
    ├── specs/2026-05-19-research-agent-design.md
    └── plans/2026-05-19-research-agent.md
```
