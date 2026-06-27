import pytest

from quorum.llm.errors import OpenRouterResponseError, extract_completion_content


def test_extract_content_success():
    raw = {
        "choices": [{"message": {"content": "Hello council"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2},
    }
    assert extract_completion_content(raw, model="test/model") == "Hello council"


def test_extract_content_uses_reasoning_fallback():
    raw = {
        "choices": [{
            "message": {"content": None, "reasoning": "Thinking hard"},
            "finish_reason": "stop",
        }],
    }
    assert extract_completion_content(raw) == "Thinking hard"


def test_extract_content_null_message():
    raw = {"choices": [{"message": None, "finish_reason": "stop"}]}
    with pytest.raises(OpenRouterResponseError, match="no message"):
        extract_completion_content(raw, model="deepseek/deepseek-v4-flash")


def test_extract_content_null_content():
    raw = {
        "choices": [{
            "message": {"content": None},
            "finish_reason": "stop",
        }],
    }
    with pytest.raises(OpenRouterResponseError, match="no assistant content"):
        extract_completion_content(raw)


def test_extract_content_blank_content():
    raw = {
        "choices": [{
            "message": {"content": "   "},
            "finish_reason": "length",
        }],
    }
    with pytest.raises(OpenRouterResponseError, match="blank assistant content"):
        extract_completion_content(raw)


def test_extract_content_api_error():
    raw = {"error": {"message": "Rate limit exceeded"}}
    with pytest.raises(OpenRouterResponseError, match="Rate limit"):
        extract_completion_content(raw)


def test_extract_content_no_choices():
    raw = {"choices": []}
    with pytest.raises(OpenRouterResponseError, match="no choices"):
        extract_completion_content(raw)
