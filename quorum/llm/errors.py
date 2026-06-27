from __future__ import annotations


class OpenRouterResponseError(Exception):
    """OpenRouter returned an unexpected or empty completion."""

    def __init__(
        self,
        message: str,
        *,
        model: str = "",
        finish_reason: str | None = None,
        raw: dict | None = None,
    ) -> None:
        self.model = model
        self.finish_reason = finish_reason
        self.raw = raw
        detail = message
        if model:
            detail = f"{model}: {message}"
        if finish_reason:
            detail = f"{detail} (finish_reason={finish_reason})"
        super().__init__(detail)


def extract_completion_content(raw: dict, *, model: str = "") -> str:
    """Parse assistant text from an OpenRouter chat completion response."""
    error = raw.get("error")
    if error:
        if isinstance(error, dict):
            msg = error.get("message") or str(error)
        else:
            msg = str(error)
        raise OpenRouterResponseError(msg, model=model, raw=raw)

    choices = raw.get("choices")
    if not choices:
        raise OpenRouterResponseError("response contained no choices", model=model, raw=raw)

    choice = choices[0] or {}
    message = choice.get("message")
    if not isinstance(message, dict):
        raise OpenRouterResponseError("choice had no message object", model=model, raw=raw)

    finish_reason = choice.get("finish_reason")
    content = message.get("content")

    # Some reasoning models put text in alternate fields when content is null.
    if content is None:
        for key in ("reasoning", "reasoning_content", "text"):
            alt = message.get(key)
            if isinstance(alt, str) and alt.strip():
                content = alt
                break

    if content is None:
        raise OpenRouterResponseError(
            "response had no assistant content",
            model=model,
            finish_reason=finish_reason,
            raw=raw,
        )

    text = content.strip() if isinstance(content, str) else str(content).strip()
    if not text:
        raise OpenRouterResponseError(
            "response had blank assistant content",
            model=model,
            finish_reason=finish_reason,
            raw=raw,
        )
    return text
