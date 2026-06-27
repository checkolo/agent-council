from __future__ import annotations

import os

MINIMAX_M3 = "minimax/minimax-m3:exacto"
DEEPSEEK_V4_FLASH = "deepseek/deepseek-v4-flash"

# Shared extras appended to every panel role's model picker.
PANEL_EXTRA_MODELS: tuple[str, ...] = (MINIMAX_M3, DEEPSEEK_V4_FLASH)

# Panel analyses are short; judge deliverables can be full specs/plans/songs.
DEFAULT_PANEL_MAX_TOKENS = 4096
DEFAULT_JUDGE_MAX_TOKENS = 131_072

# OpenRouter model slugs available for judge override in the UI.
JUDGE_MODELS: list[str] = [
    "anthropic/claude-sonnet-4",
    MINIMAX_M3,
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
]


def panel_suggested_models(*models: str) -> list[str]:
    """Role defaults plus shared panel extras for model override UI."""
    seen: set[str] = set()
    result: list[str] = []
    for model in (*models, *PANEL_EXTRA_MODELS):
        if model not in seen:
            seen.add(model)
            result.append(model)
    return result


def resolve_panel_max_tokens() -> int | None:
    """Max completion tokens for council panel members."""
    raw = os.environ.get("QUORUM_PANEL_MAX_TOKENS", "")
    if not raw:
        return DEFAULT_PANEL_MAX_TOKENS
    value = int(raw)
    return None if value <= 0 else value


def resolve_judge_max_tokens(override: int | None = None) -> int | None:
    """Max completion tokens for judge synthesis.

    Set QUORUM_JUDGE_MAX_TOKENS=0 to omit the limit and defer to the provider.
    """
    if override is not None:
        return None if override <= 0 else override
    raw = os.environ.get("QUORUM_JUDGE_MAX_TOKENS", "")
    if raw:
        value = int(raw)
        return None if value <= 0 else value
    return DEFAULT_JUDGE_MAX_TOKENS
