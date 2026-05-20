import pytest

from research import parse_query, check_api_key, build_options


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
        captured = capsys.readouterr()
        assert "Usage" in captured.err


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
        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY" in captured.err


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
