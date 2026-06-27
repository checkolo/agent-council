from __future__ import annotations

import json
import string


def anonymize_outputs(
    outputs: list[dict],
    exclude_role: str | None = None,
) -> tuple[str, dict[str, str]]:
    """Anonymize member outputs as Reviewer A, B, etc. Returns text + alias map."""
    aliases = {}
    letters = iter(string.ascii_uppercase)
    lines = []

    for output in outputs:
        if exclude_role and output["role"] == exclude_role:
            continue
        alias = next(letters)
        aliases[alias] = output["role"]
        lines.append(f"### Reviewer {alias}\n{output['content']}\n")

    return "\n".join(lines), aliases


def parse_peer_review(content: str) -> dict | None:
    """Try to parse peer review JSON from model output."""
    import re

    match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
    raw = match.group(1) if match else content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]*\"rankings\"[\s\S]*\})", content)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None
