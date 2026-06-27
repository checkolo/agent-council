from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

from quorum.council.decision import (
    DecisionReport,
    MemberOutput,
    PeerReview,
    parse_decision_report,
)
from quorum.council.prompts import judge_prompt, panel_prompt, peer_reviewer_prompt
from quorum.council.review import anonymize_outputs, parse_peer_review
from quorum.council.roles import ROLES, get_role
from quorum.council.models import resolve_judge_max_tokens, resolve_panel_max_tokens
from quorum.llm.openrouter import OpenRouterClient
from quorum.storage.sqlite import Storage

Mode = Literal["fast", "thorough"]
EventCallback = Callable[[str, dict], None]


@dataclass
class OutcomeOption:
    id: str
    label: str
    description: str
    instruction: str


@dataclass
class Template:
    name: str
    description: str
    roles: list[str]
    judge_model: str
    mode: Mode = "fast"
    max_cost_usd: float = 0.50
    default_outcome: str = "review-report"
    outcomes: list[OutcomeOption] = field(default_factory=list)


@dataclass
class RunContext:
    run_id: str
    template: Template
    input_text: str
    mode: Mode
    max_cost: float | None = None
    model_overrides: dict[str, str] = field(default_factory=dict)
    desired_outcome: str | None = None
    judge_max_tokens: int | None = None
    on_event: EventCallback | None = None


def load_template(name: str, templates_dir: Path | None = None) -> Template:
    base = templates_dir or Path("templates")
    path = base / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {name}")
    data = yaml.safe_load(path.read_text())
    outcomes = [
        OutcomeOption(
            id=o["id"],
            label=o["label"],
            description=o.get("description", ""),
            instruction=o.get("instruction", ""),
        )
        for o in data.get("outcomes", [])
    ]
    default_outcome = data.get("default_outcome", outcomes[0].id if outcomes else "review-report")
    return Template(
        name=data["name"],
        description=data.get("description", ""),
        roles=data["roles"],
        judge_model=data.get("judge_model", "anthropic/claude-sonnet-4"),
        mode=data.get("mode", "fast"),
        max_cost_usd=data.get("max_cost_usd", 0.50),
        default_outcome=default_outcome,
        outcomes=outcomes,
    )


def resolve_outcome(template: Template, outcome_id: str | None) -> OutcomeOption | None:
    if not template.outcomes:
        return None
    chosen = outcome_id or template.default_outcome
    for o in template.outcomes:
        if o.id == chosen:
            return o
    return template.outcomes[0]


def list_templates(templates_dir: Path | None = None) -> list[Template]:
    base = templates_dir or Path("templates")
    templates = []
    for path in sorted(base.glob("*.yaml")):
        try:
            templates.append(load_template(path.stem, base))
        except (KeyError, yaml.YAMLError):
            continue
    return templates


class CostCapExceeded(Exception):
    pass


async def run_task(
    ctx: RunContext,
    client: OpenRouterClient,
    storage: Storage | None = None,
) -> DecisionReport:
    """Run the council engine: panel → (optional peer review) → judge."""
    start = time.monotonic()
    template = ctx.template
    mode = ctx.mode
    member_outputs: list[MemberOutput] = []
    peer_reviews: list[PeerReview] = []

    def emit(event_type: str, payload: dict, member: str | None = None) -> None:
        if ctx.on_event:
            ctx.on_event(event_type, {"member": member, **payload})
        if storage:
            storage.add_event(ctx.run_id, event_type, payload, member)

    def check_cost() -> None:
        if ctx.max_cost and client.total_cost_usd > ctx.max_cost:
            raise CostCapExceeded(
                f"Cost cap ${ctx.max_cost:.2f} exceeded (current: ${client.total_cost_usd:.4f})"
            )

    task_desc = f"Template: {template.name}\n\nInput:\n{ctx.input_text[:8000]}"
    panel_max_tokens = resolve_panel_max_tokens()
    judge_max_tokens = resolve_judge_max_tokens(ctx.judge_max_tokens)
    judge_timeout = 600.0

    # Phase 1: Panel (parallel)
    async def run_member(role_name: str) -> MemberOutput:
        role = get_role(role_name)
        model = ctx.model_overrides.get(role_name, role.suggested_models[0])
        system = panel_prompt(role.display_name, role.system_prompt, task_desc)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": ctx.input_text},
        ]
        check_cost()
        try:
            result = await client.chat_completion(
                model, messages, max_tokens=panel_max_tokens, retries=1
            )
        except Exception as exc:
            raise RuntimeError(f"Panel member {role.display_name} ({model}) failed: {exc}") from exc
        content = result["content"]
        preview = content[:100] if content else ""
        emit("panel.token", {"token": preview, "role": role_name}, role_name)
        emit("panel.done", {"content": content, "role": role_name, "model": model}, role_name)
        return MemberOutput(role=role.display_name, model=model, content=content)

    panel_results = await asyncio.gather(
        *[run_member(r) for r in template.roles],
        return_exceptions=True,
    )
    member_outputs: list[MemberOutput] = []
    panel_errors: list[str] = []
    for role_name, result in zip(template.roles, panel_results, strict=True):
        if isinstance(result, Exception):
            panel_errors.append(str(result))
            continue
        member_outputs.append(result)
    if not member_outputs:
        raise RuntimeError(
            "All panel members failed: " + "; ".join(panel_errors)
        )
    if panel_errors:
        emit("panel.partial", {"errors": panel_errors, "completed": len(member_outputs)})

    # Phase 2: Peer review (thorough mode only)
    peer_review_text = ""
    if mode == "thorough":
        outputs_dicts = [{"role": m.role, "content": m.content} for m in member_outputs]

        async def run_peer(reviewer: MemberOutput) -> PeerReview:
            role_key = next(
                (k for k, r in ROLES.items() if r.display_name == reviewer.role),
                "architect",
            )
            anonymized, _ = anonymize_outputs(outputs_dicts, exclude_role=reviewer.role)
            model = ctx.model_overrides.get(role_key, get_role(role_key).suggested_models[0])
            messages = [
                {"role": "system", "content": peer_reviewer_prompt(len(template.roles) - 1)},
                {"role": "user", "content": anonymized},
            ]
            check_cost()
            try:
                result = await client.chat_completion(
                    model, messages, max_tokens=panel_max_tokens, retries=1
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Peer review by {reviewer.role} ({model}) failed: {exc}"
                ) from exc
            content = result["content"]
            parsed = parse_peer_review(content)
            preview = content[:100] if content else ""
            emit("review.token", {"token": preview}, reviewer.role)
            emit("review.done", {"content": content, "parsed": parsed}, reviewer.role)
            return PeerReview(reviewer_role=reviewer.role, content=content, parsed=parsed)

        peer_results = await asyncio.gather(*[run_peer(m) for m in member_outputs])
        peer_reviews = list(peer_results)
        peer_review_text = "\n\n".join(
            f"### {pr.reviewer_role}\n{pr.content}" for pr in peer_reviews
        )

    # Phase 3: Judge
    member_text = "\n\n".join(
        f"### {m.role} ({m.model})\n{m.content}" for m in member_outputs
    )
    judge_model = ctx.model_overrides.get("judge", template.judge_model)
    outcome = resolve_outcome(template, ctx.desired_outcome)
    judge_system = judge_prompt(
        task_desc,
        member_text,
        peer_review_text,
        outcome_instruction=outcome.instruction if outcome else "",
        outcome_label=outcome.label if outcome else "",
    )
    judge_messages = [
        {"role": "system", "content": judge_system},
        {"role": "user", "content": "Produce the DecisionReport now."},
    ]

    check_cost()
    try:
        judge_result = await client.chat_completion(
            judge_model,
            judge_messages,
            max_tokens=judge_max_tokens,
            timeout=judge_timeout,
            retries=1,
        )
    except Exception as exc:
        raise RuntimeError(f"Judge ({judge_model}) failed: {exc}") from exc
    judge_content = judge_result["content"]
    emit("judge.token", {"token": judge_content})
    emit("judge.done", {"content": judge_content})

    duration_ms = int((time.monotonic() - start) * 1000)

    async def retry_judge() -> str:
        retry_messages = judge_messages + [
            {"role": "assistant", "content": judge_content},
            {
                "role": "user",
                "content": (
                    "Your output was not valid JSON. Please output the DecisionReport "
                    "with a ```json block containing consensus, disagreements, risks, "
                    "unknowns, recommendation, and attribution fields."
                ),
            },
        ]
        check_cost()
        retry_result = await client.chat_completion(
            judge_model,
            retry_messages,
            max_tokens=judge_max_tokens,
            timeout=judge_timeout,
            retries=1,
        )
        return retry_result["content"]

    report = parse_decision_report(
        judge_content,
        task_id=ctx.run_id,
        template=template.name,
        member_outputs=member_outputs,
        peer_reviews=peer_reviews,
        cost_usd=client.total_cost_usd,
        duration_ms=duration_ms,
        retry_fn=lambda: asyncio.get_event_loop().run_until_complete(retry_judge())
        if False
        else None,
    )

    # Retry once for valid JSON when markdown fallback lacks a usable deliverable.
    if (
        report.markdown_fallback
        and client.api_key
        and len(report.deliverable.strip()) < 80
    ):
        try:
            retry_content = await retry_judge()
            retry_report = parse_decision_report(
                retry_content,
                task_id=ctx.run_id,
                template=template.name,
                member_outputs=member_outputs,
                peer_reviews=peer_reviews,
                cost_usd=client.total_cost_usd,
                duration_ms=duration_ms,
            )
            if not retry_report.markdown_fallback or len(
                retry_report.deliverable.strip()
            ) >= len(report.deliverable.strip()):
                report = retry_report
        except Exception:
            pass

    report.cost_usd = client.total_cost_usd
    report.duration_ms = duration_ms

    emit("run.done", {
        "cost_usd": report.cost_usd,
        "duration_ms": duration_ms,
        "status": "complete",
    })

    if storage:
        storage.update_run(
            ctx.run_id,
            status="complete",
            decision_report=report.model_dump(),
            cost_usd=report.cost_usd,
            duration_ms=duration_ms,
        )

    return report


async def run_and_export(
    ctx: RunContext,
    client: OpenRouterClient,
    storage: Storage,
    export_dir: Path | None = None,
) -> tuple[DecisionReport, Path | None]:
    report = await run_task(ctx, client, storage)
    run_data = {
        "run_id": ctx.run_id,
        "template": ctx.template.name,
        "input": ctx.input_text,
        "mode": ctx.mode,
        "decision_report": report.model_dump(),
        "events": storage.get_events(ctx.run_id),
    }
    out_dir = export_dir or Path("cassettes/samples")
    out_dir.mkdir(parents=True, exist_ok=True)
    cassette_path = export_cassette(run_data, out_dir / f"{ctx.run_id}")
    report.cassette_path = str(cassette_path)
    return report, cassette_path
