from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class Risk(BaseModel):
    description: str
    severity: Literal["blocker", "major", "minor", "nit"] = "minor"


class Disagreement(BaseModel):
    topic: str
    positions: dict[str, str] = Field(default_factory=dict)
    resolution: str = ""
    chosen_position: str = ""


class Recommendation(BaseModel):
    action: str
    evidence: list[str] = Field(default_factory=list)


class Attribution(BaseModel):
    role: str
    idea: str


class MemberOutput(BaseModel):
    role: str
    model: str
    content: str
    alias: str | None = None


class PeerReview(BaseModel):
    reviewer_role: str
    content: str
    parsed: dict | None = None


class DecisionReport(BaseModel):
    task_id: str = ""
    template: str = ""
    deliverable: str = ""
    consensus: list[str] = Field(default_factory=list)
    disagreements: list[Disagreement] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    recommendation: Recommendation = Field(default_factory=lambda: Recommendation(action=""))
    attribution: list[Attribution] = Field(default_factory=list)
    member_outputs: list[MemberOutput] = Field(default_factory=list)
    peer_reviews: list[PeerReview] = Field(default_factory=list)
    cost_usd: float = 0.0
    duration_ms: int = 0
    cassette_path: str = ""
    markdown_fallback: str | None = None


def extract_json_block(text: str) -> dict | None:
    """Extract JSON from markdown code fence or raw JSON."""
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"(\{[\s\S]*\"(?:consensus|deliverable)\"[\s\S]*\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    return None


def parse_markdown_sections(text: str) -> dict:
    """Fallback parser for markdown-only judge output."""
    section_keys = {
        "deliverable",
        "consensus",
        "disagreements",
        "risks",
        "unknowns",
        "recommendation",
        "attribution",
    }
    sections: dict[str, list[str]] = {key: [] for key in section_keys}
    current: str | None = None
    for line in text.split("\n"):
        header_match = re.match(r"^##\s+(.+?)\s*$", line, re.IGNORECASE)
        if header_match:
            key = header_match.group(1).strip().lower()
            current = key if key in section_keys else None
            continue
        if current is None:
            continue
        if current == "deliverable":
            sections[current].append(line)
        elif line.strip().startswith("-"):
            sections[current].append(line.strip().lstrip("- ").strip())
    return sections


def parse_decision_report(
    judge_output: str,
    *,
    task_id: str = "",
    template: str = "",
    member_outputs: list[MemberOutput] | None = None,
    peer_reviews: list[PeerReview] | None = None,
    cost_usd: float = 0.0,
    duration_ms: int = 0,
    retry_fn=None,
) -> DecisionReport:
    """Parse judge output with JSON extraction, retry, and markdown fallback."""
    data = extract_json_block(judge_output)

    if data is None and retry_fn:
        retry_output = retry_fn()
        data = extract_json_block(retry_output)
        if data is None:
            judge_output = retry_output

    if data:
        try:
            report = DecisionReport(
                task_id=task_id,
                template=template,
                deliverable=data.get("deliverable", ""),
                consensus=data.get("consensus", []),
                disagreements=[Disagreement(**d) for d in data.get("disagreements", [])],
                risks=[Risk(**r) for r in data.get("risks", [])],
                unknowns=data.get("unknowns", []),
                recommendation=Recommendation(**data.get("recommendation", {"action": ""})),
                attribution=[Attribution(**a) for a in data.get("attribution", [])],
                member_outputs=member_outputs or [],
                peer_reviews=peer_reviews or [],
                cost_usd=cost_usd,
                duration_ms=duration_ms,
            )
            return report
        except (ValidationError, TypeError):
            pass

    sections = parse_markdown_sections(judge_output)
    deliverable_lines = sections["deliverable"]
    deliverable_text = "\n".join(deliverable_lines).strip()
    return DecisionReport(
        task_id=task_id,
        template=template,
        deliverable=deliverable_text,
        consensus=sections["consensus"],
        disagreements=[
            Disagreement(topic=d, positions={}, resolution="")
            for d in sections["disagreements"]
        ],
        risks=[
            Risk(description=r, severity="minor") for r in sections["risks"]
        ],
        unknowns=sections["unknowns"],
        recommendation=Recommendation(
            action=sections["recommendation"][0] if sections["recommendation"] else "",
            evidence=sections["recommendation"][1:] if len(sections["recommendation"]) > 1 else [],
        ),
        attribution=[
            Attribution(role="unknown", idea=a) for a in sections["attribution"]
        ],
        member_outputs=member_outputs or [],
        peer_reviews=peer_reviews or [],
        cost_usd=cost_usd,
        duration_ms=duration_ms,
        markdown_fallback=judge_output,
    )


def render_markdown(report: DecisionReport) -> str:
    lines = ["# Decision Report", ""]

    if report.deliverable:
        lines.append("## Deliverable")
        lines.append(report.deliverable)
        lines.append("")

    lines.append("## Consensus")
    for item in report.consensus:
        lines.append(f"- {item}")
    if not report.consensus:
        lines.append("- (none identified)")
    lines.append("")

    lines.append("## Disagreements")
    for d in report.disagreements:
        lines.append(f"- **{d.topic}**")
        for role, pos in d.positions.items():
            lines.append(f"  - {role}: {pos}")
        if d.resolution:
            lines.append(f"  - Resolution: {d.resolution}")
    if not report.disagreements:
        lines.append("- (none identified)")
    lines.append("")

    lines.append("## Risks")
    for r in report.risks:
        lines.append(f"- [{r.severity}] {r.description}")
    if not report.risks:
        lines.append("- (none identified)")
    lines.append("")

    lines.append("## Unknowns")
    for u in report.unknowns:
        lines.append(f"- {u}")
    if not report.unknowns:
        lines.append("- (none identified)")
    lines.append("")

    lines.append("## Recommendation")
    lines.append(f"- {report.recommendation.action}")
    for ev in report.recommendation.evidence:
        lines.append(f"  > {ev}")
    lines.append("")

    lines.append("## Attribution")
    for a in report.attribution:
        lines.append(f"- [{a.role}] → {a.idea}")

    return "\n".join(lines)


def render_rich(report: DecisionReport, console) -> None:
    from rich.markdown import Markdown
    from rich.panel import Panel

    console.print(Panel(Markdown(render_markdown(report)), title="Decision Report", border_style="white"))
