from __future__ import annotations

from dataclasses import dataclass

from quorum.council.models import panel_suggested_models


@dataclass
class Role:
    name: str
    display_name: str
    system_prompt: str
    suggested_models: list[str]


ROLES: dict[str, Role] = {
    "architect": Role(
        name="architect",
        display_name="Architect",
        system_prompt="module boundaries, dependencies, coupling, evolution, failure modes, alternatives not taken",
        suggested_models=panel_suggested_models("anthropic/claude-sonnet-4", "openai/gpt-4o-mini"),
    ),
    "security": Role(
        name="security",
        display_name="Security Reviewer",
        system_prompt=(
            "threat model, trust boundaries, attack surface, CVEs, "
            "input validation, authn/z, secrets handling"
        ),
        suggested_models=panel_suggested_models("anthropic/claude-sonnet-4", "openai/gpt-4o-mini"),
    ),
    "performance": Role(
        name="performance",
        display_name="Performance Engineer",
        system_prompt="hot paths, complexity, allocation, I/O, caching, concurrency, measurement plan",
        suggested_models=panel_suggested_models("openai/gpt-4o-mini", "google/gemini-2.0-flash-001"),
    ),
    "qa": Role(
        name="qa",
        display_name="QA Engineer",
        system_prompt="testability, missing test cases, edge cases, flakiness, observability hooks",
        suggested_models=panel_suggested_models("openai/gpt-4o-mini", "anthropic/claude-3.5-haiku"),
    ),
    "lyricist": Role(
        name="lyricist",
        display_name="Lyricist",
        system_prompt=(
            "narrative arc, rhyme and meter, imagery, emotional resonance, "
            "hook lines, theme consistency, singability of words"
        ),
        suggested_models=panel_suggested_models("anthropic/claude-sonnet-4", "openai/gpt-4o-mini"),
    ),
    "melody": Role(
        name="melody",
        display_name="Melody Composer",
        system_prompt=(
            "melodic contour, phrasing, singability, key and mode, "
            "motifs, verse-chorus contrast, rhythmic feel"
        ),
        suggested_models=panel_suggested_models("anthropic/claude-sonnet-4", "openai/gpt-4o-mini"),
    ),
    "producer": Role(
        name="producer",
        display_name="Producer",
        system_prompt=(
            "song structure, dynamics, instrumentation, tempo, genre fit, "
            "arrangement layers, intro/outro, production texture"
        ),
        suggested_models=panel_suggested_models("openai/gpt-4o-mini", "anthropic/claude-sonnet-4"),
    ),
    "critic": Role(
        name="critic",
        display_name="Music Critic",
        system_prompt=(
            "market appeal, originality, coherence with the brief, audience fit, "
            "memorability, clichés to avoid, comparative references"
        ),
        suggested_models=panel_suggested_models("openai/gpt-4o-mini", "anthropic/claude-3.5-haiku"),
    ),
}


def get_role(name: str) -> Role:
    if name not in ROLES:
        raise ValueError(f"Unknown role: {name}. Available: {list(ROLES.keys())}")
    return ROLES[name]
