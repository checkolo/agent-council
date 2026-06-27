#!/usr/bin/env python3
"""Generate sample cassettes for keyless demo."""
import json
import zipfile
from pathlib import Path

SAMPLES = [
    {
        "run_id": "demo-auth",
        "template": "pr-review",
        "input": Path("tests/fixtures/sample.diff").read_text(),
        "mode": "fast",
        "decision_report": {
            "task_id": "demo-auth",
            "template": "pr-review",
            "consensus": [
                "Token comparison must use constant-time comparison",
                "Password hashing should not use MD5",
            ],
            "disagreements": [
                {
                    "topic": "Salt storage format",
                    "positions": {
                        "Architect": "Store salt separately in DB column",
                        "Security Reviewer": "Embed salt in hash string",
                    },
                    "resolution": "Embed salt in hash string for simpler migration",
                    "chosen_position": "Security Reviewer",
                }
            ],
            "risks": [
                {"description": "Missing hmac import will cause runtime error", "severity": "blocker"},
                {"description": "Existing MD5 hashes need migration path", "severity": "major"},
            ],
            "unknowns": ["Whether API_TOKEN is always set in production"],
            "recommendation": {
                "action": "Add hmac import and migration for existing password hashes",
                "evidence": ["Security Reviewer → hmac.compare_digest", "QA Engineer → add migration tests"],
            },
            "attribution": [
                {"role": "Security Reviewer", "idea": "Use hmac.compare_digest for token verification"},
                {"role": "Architect", "idea": "Separate salt storage for cleaner schema"},
                {"role": "QA Engineer", "idea": "Add tests for timing-safe comparison"},
            ],
            "member_outputs": [
                {
                    "role": "Architect",
                    "model": "anthropic/claude-sonnet-4",
                    "content": "## Findings\n1. [major] Module boundary change mixes auth concerns\n\n## Evidence\n- verify_token now depends on hmac\n\n## Recommendation\n- Extract crypto utilities to separate module\n\n## Confidence\n- medium — limited context on deployment",
                },
                {
                    "role": "Security Reviewer",
                    "model": "anthropic/claude-sonnet-4",
                    "content": "## Findings\n1. [blocker] Missing hmac import\n2. [major] MD5 replaced with pbkdf2 but no migration\n\n## Evidence\n- Line 13: hmac.compare_digest used but hmac not imported\n\n## Recommendation\n- Add hmac import and hash migration strategy\n\n## Confidence\n- high — clear security issues",
                },
                {
                    "role": "Performance Engineer",
                    "model": "openai/gpt-4o-mini",
                    "content": "## Findings\n1. [minor] pbkdf2 with 100k iterations adds ~100ms per login\n\n## Evidence\n- hash_password uses 100000 iterations\n\n## Recommendation\n- Consider caching for high-traffic endpoints\n\n## Confidence\n- medium — depends on traffic patterns",
                },
                {
                    "role": "QA Engineer",
                    "model": "openai/gpt-4o-mini",
                    "content": "## Findings\n1. [major] No tests for new hash_password\n2. [minor] Missing test for empty API_TOKEN\n\n## Evidence\n- No test file changes in diff\n\n## Recommendation\n- Add unit tests for verify_token edge cases\n\n## Confidence\n- high — test gap is clear",
                },
            ],
            "peer_reviews": [],
            "cost_usd": 0.07,
            "duration_ms": 18234,
        },
    },
    {
        "run_id": "demo-arch",
        "template": "architecture-review",
        "input": "Design review: microservices auth layer with shared token validation",
        "mode": "thorough",
        "decision_report": {
            "task_id": "demo-arch",
            "template": "architecture-review",
            "consensus": [
                "Shared auth library reduces duplication across services",
                "Token validation should be stateless where possible",
            ],
            "disagreements": [],
            "risks": [
                {"description": "Shared library versioning across services", "severity": "major"},
            ],
            "unknowns": ["Current service count and deployment cadence"],
            "recommendation": {
                "action": "Extract auth into versioned shared library with semver",
                "evidence": ["Architect → module boundaries"],
            },
            "attribution": [
                {"role": "Architect", "idea": "Versioned shared auth library"},
            ],
            "member_outputs": [],
            "peer_reviews": [],
            "cost_usd": 0.15,
            "duration_ms": 45000,
        },
    },
]

out_dir = Path("cassettes/samples")
out_dir.mkdir(parents=True, exist_ok=True)

for sample in SAMPLES:
    path = out_dir / f"{sample['run_id']}.cassette"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps({"version": "0.1", "run_id": sample["run_id"]}, indent=2))
        zf.writestr("run.json", json.dumps(sample, indent=2))
    print(f"Created {path}")
