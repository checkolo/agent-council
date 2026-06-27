from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

from quorum.llm.errors import OpenRouterResponseError, extract_completion_content

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Approximate cost per 1M tokens (USD) for common models
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "openai/gpt-4o-mini": (0.15, 0.60),
    "anthropic/claude-sonnet-4": (3.0, 15.0),
    "anthropic/claude-3.5-haiku": (0.80, 4.0),
    "google/gemini-2.0-flash-001": (0.10, 0.40),
    "minimax/minimax-m3:exacto": (0.30, 1.20),
    "deepseek/deepseek-v4-flash": (0.10, 0.40),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = MODEL_COSTS.get(model, (1.0, 3.0))
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


def _format_http_error(model: str, response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return f"{model}: HTTP {response.status_code} — {response.text[:300]}"
    error = payload.get("error")
    if isinstance(error, dict):
        msg = error.get("message") or str(error)
    elif error:
        msg = str(error)
    else:
        msg = response.text[:300] or f"HTTP {response.status_code}"
    return f"{model}: {msg}"


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        recorded: bool = False,
        cassette_dir: Path | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.recorded = recorded
        self.cassette_dir = cassette_dir or Path(
            os.environ.get("QUORUM_CASSETTE_DIR", "cassettes")
        )
        self._usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}
        self._cost_usd = 0.0

    @property
    def total_cost_usd(self) -> float:
        return self._cost_usd

    @property
    def total_tokens(self) -> dict[str, int]:
        return dict(self._usage)

    def _cassette_key(self, model: str, messages: list[dict[str, str]]) -> str:
        payload = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def _cassette_path(self, key: str) -> Path:
        return self.cassette_dir / "recordings" / f"{key}.json"

    def _load_cassette(self, key: str) -> dict[str, Any] | None:
        path = self._cassette_path(key)
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _save_cassette(self, key: str, data: dict[str, Any]) -> None:
        path = self._cassette_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def _finalize_result(self, model: str, raw: dict[str, Any]) -> dict[str, Any]:
        content = extract_completion_content(raw, model=model)
        usage = raw.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = estimate_cost(model, prompt_tokens, completion_tokens)

        self._usage["prompt_tokens"] += prompt_tokens
        self._usage["completion_tokens"] += completion_tokens
        self._cost_usd += cost

        return {
            "content": content,
            "model": model,
            "usage": usage,
            "cost_usd": cost,
            "raw": raw,
        }

    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        stream: bool = False,
        max_tokens: int | None = 4096,
        timeout: float = 120.0,
        retries: int = 1,
    ) -> dict[str, Any]:
        key = self._cassette_key(model, messages)

        if self.recorded or not self.api_key:
            cached = self._load_cassette(key)
            if cached:
                usage = cached.get("usage") or {}
                self._usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                self._usage["completion_tokens"] += usage.get("completion_tokens", 0)
                self._cost_usd += cached.get("cost_usd", 0.0)
                # Re-validate cached payloads so bad recordings fail loudly.
                content = cached.get("content")
                if not content or not str(content).strip():
                    extract_completion_content(cached.get("raw") or {}, model=model)
                return cached

            if self.recorded:
                raise FileNotFoundError(
                    f"No cassette for key {key}. Record first with --record."
                )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/quorum-council/quorum",
            "X-Title": "Quorum",
        }
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        last_error: Exception | None = None
        attempts = max(1, retries + 1)
        for attempt in range(attempts):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(OPENROUTER_URL, headers=headers, json=body)
                    try:
                        resp.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        raise OpenRouterResponseError(
                            _format_http_error(model, exc.response),
                            model=model,
                        ) from exc
                    raw = resp.json()

                result = self._finalize_result(model, raw)
                self._save_cassette(key, result)
                return result
            except OpenRouterResponseError as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    raise
        raise last_error  # pragma: no cover
