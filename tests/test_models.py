from quorum.council.models import (
    DEFAULT_JUDGE_MAX_TOKENS,
    resolve_judge_max_tokens,
    resolve_panel_max_tokens,
)


def test_judge_max_tokens_default():
    assert resolve_judge_max_tokens() == DEFAULT_JUDGE_MAX_TOKENS
    assert DEFAULT_JUDGE_MAX_TOKENS > 8192


def test_judge_max_tokens_override():
    assert resolve_judge_max_tokens(65536) == 65536
    assert resolve_judge_max_tokens(0) is None


def test_panel_max_tokens_default():
    assert resolve_panel_max_tokens() == 4096
