from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from quorum import __version__
from quorum.council.decision import render_markdown, render_rich
from quorum.council.engine import (
    CostCapExceeded,
    RunContext,
    list_templates,
    load_template,
    run_task,
)
from quorum.llm.cassettes import export_cassette, import_cassette
from quorum.llm.openrouter import OpenRouterClient
from quorum.storage.sqlite import Storage

app = typer.Typer(
    name="quorum",
    help="Multi-role code review with replayable Decision Reports.",
    no_args_is_help=True,
)
console = Console()
serve_app = typer.Typer(help="Start the Quorum server.")
app.add_typer(serve_app, name="serve")


def _get_storage() -> Storage:
    return Storage()


def _read_input(file: Path | None, stdin: bool) -> str:
    if file:
        if not file.exists():
            raise typer.BadParameter(f"File not found: {file}")
        if not file.is_file():
            raise typer.BadParameter(f"Not a file: {file}")
        return file.read_text()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise typer.BadParameter(
        "Provide --file PATH, pipe stdin, e.g. "
        "quorum run -t song-writer -f tests/fixtures/song-brief.txt --record"
    )


@app.command()
def version():
    """Show version."""
    console.print(f"quorum v{__version__}")


@app.command("self-test")
def self_test():
    """Verify SQLite storage works."""
    storage = _get_storage()
    ok = storage.self_test()
    if ok:
        console.print("[green]✓[/green] Storage self-test passed.")
        raise typer.Exit(0)
    console.print("[red]✗[/red] Storage self-test failed.")
    raise typer.Exit(1)


@app.command()
def call(
    model: str,
    message: str,
    recorded: Annotated[bool, typer.Option("--recorded", help="Use recorded cassettes")] = False,
    record: Annotated[bool, typer.Option("--record", help="Record response to cassette")] = False,
):
    """Make a single LLM call (for testing cassettes)."""
    async def _run():
        client = OpenRouterClient(recorded=recorded or not bool(__import__("os").environ.get("OPENROUTER_API_KEY")))
        if record:
            client.recorded = False
        result = await client.chat_completion(model, [{"role": "user", "content": message}])
        console.print(result["content"])
        console.print(f"\n[dim]Cost: ${result.get('cost_usd', 0):.4f}[/dim]")

    asyncio.run(_run())


@app.command()
def templates():
    """List available review templates."""
    table = Table(title="Templates")
    table.add_column("Name", style="bold")
    table.add_column("Roles")
    table.add_column("Mode")
    table.add_column("Max Cost")
    for t in list_templates():
        table.add_row(t.name, ", ".join(t.roles), t.mode, f"${t.max_cost_usd:.2f}")
    console.print(table)


@app.command()
def run(
    template: Annotated[str, typer.Option("--template", "-t")] = "pr-review",
    file: Annotated[Path | None, typer.Option("--file", "-f")] = None,
    mode: Annotated[str, typer.Option("--mode", "-m")] = "fast",
    max_cost: Annotated[float | None, typer.Option("--max-cost")] = None,
    recorded: Annotated[bool, typer.Option("--recorded", help="Replay from cassettes")] = False,
    record: Annotated[bool, typer.Option("--record", help="Record LLM calls")] = False,
    out: Annotated[Path | None, typer.Option("--out", "-o")] = None,
):
    """Run a council review on input."""
    async def _run():
        storage = _get_storage()
        try:
            tmpl = load_template(template)
        except FileNotFoundError:
            console.print(f"[red]Template not found:[/red] {template}")
            raise typer.Exit(1)

        try:
            input_text = _read_input(file, True)
        except typer.BadParameter as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

        run_id = storage.create_run(template, input_text, mode, max_cost)
        console.print(f"[dim]Run ID:[/dim] {run_id}")

        client = OpenRouterClient(recorded=recorded)
        if record:
            client.recorded = False

        ctx = RunContext(
            run_id=run_id,
            template=tmpl,
            input_text=input_text,
            mode=mode,  # type: ignore
            max_cost=max_cost or tmpl.max_cost_usd,
        )

        console.print(
            Panel(
                f"Template: {template} · Mode: {mode} · Members: {len(tmpl.roles)}",
                title="Quorum Council",
            )
        )

        try:
            report = await run_task(ctx, client, storage)
        except CostCapExceeded as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

        render_rich(report, console)

        footer = (
            f"Cost: ${report.cost_usd:.4f} · "
            f"Duration: {report.duration_ms / 1000:.1f}s · "
            f"Run: {run_id}"
        )
        console.print(f"\n[dim]{footer}[/dim]")

        if out:
            out.write_text(render_markdown(report))
            console.print(f"[green]Saved to[/green] {out}")

        run_data = {
            "run_id": run_id,
            "template": template,
            "input": input_text,
            "mode": mode,
            "decision_report": report.model_dump(),
        }
        cassette_path = export_cassette(run_data, Path("cassettes") / run_id)
        console.print(f"[dim]Cassette:[/dim] {cassette_path}")

    asyncio.run(_run())


@app.command()
def review(
    template: Annotated[str, typer.Option("--template", "-t")] = "pr-review",
    file: Annotated[Path | None, typer.Option("--file", "-f")] = None,
    focus: Annotated[str | None, typer.Option("--focus")] = None,
    mode: Annotated[str, typer.Option("--mode", "-m")] = "fast",
    max_cost: Annotated[float | None, typer.Option("--max-cost")] = None,
    recorded: Annotated[bool, typer.Option("--recorded")] = False,
):
    """Review code (alias for run, optimized for gh pr diff pipe)."""
    run(
        template=template,
        file=file,
        mode=mode,
        max_cost=max_cost,
        recorded=recorded,
        record=False,
        out=None,
    )


@app.command()
def history(
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
):
    """Show recent runs."""
    storage = _get_storage()
    runs = storage.list_runs(limit=limit)
    if not runs:
        console.print("[dim]No runs yet.[/dim]")
        return
    table = Table(title=f"Recent Runs (last {limit})")
    table.add_column("ID")
    table.add_column("Template")
    table.add_column("Mode")
    table.add_column("Status")
    table.add_column("Cost")
    table.add_column("Created")
    for r in runs:
        table.add_row(
            r["id"],
            r["template"],
            r["mode"],
            r["status"],
            f"${r.get('cost_usd', 0):.4f}",
            r["created_at"][:19],
        )
    console.print(table)


@app.command()
def show(run_id: str):
    """Show a run's Decision Report."""
    storage = _get_storage()
    run = storage.get_run(run_id)
    if not run:
        console.print(f"[red]Run not found:[/red] {run_id}")
        raise typer.Exit(1)
    report_data = run.get("decision_report")
    if not report_data:
        console.print(f"[yellow]Run {run_id} has no decision report yet (status: {run['status']})[/yellow]")
        raise typer.Exit(0)
    from quorum.council.decision import DecisionReport
    report = DecisionReport(**report_data)
    render_rich(report, console)
    cost = run.get("cost_usd", 0)
    duration = run.get("duration_ms", 0) / 1000
    console.print(f"\n[dim]Cost: ${cost:.4f} · Duration: {duration:.1f}s[/dim]")


@app.command()
def export(run_id: str, output: Annotated[Path | None, typer.Option("-o")] = None):
    """Export a run to a .cassette file."""
    storage = _get_storage()
    run = storage.get_run(run_id)
    if not run:
        console.print(f"[red]Run not found:[/red] {run_id}")
        raise typer.Exit(1)
    run_data = {
        "run_id": run_id,
        "template": run["template"],
        "input": run["input_text"],
        "mode": run["mode"],
        "decision_report": run.get("decision_report"),
        "events": storage.get_events(run_id),
    }
    out = output or Path(f"{run_id}.cassette")
    path = export_cassette(run_data, out)
    console.print(f"[green]Exported[/green] {path}")


@app.command()
def replay(cassette_path: Path):
    """Replay a .cassette file offline."""
    try:
        data = import_cassette(cassette_path)
    except Exception as e:
        console.print(f"[red]Invalid cassette:[/red] {e}")
        raise typer.Exit(1)
    report_data = data.get("decision_report")
    if report_data:
        from quorum.council.decision import DecisionReport
        report = DecisionReport(**report_data)
        render_rich(report, console)
    else:
        console.print(json.dumps(data, indent=2))


@app.command()
def eval_cmd(
    suite: Annotated[Path, typer.Option("--suite")] = Path("evals/coding-questions.yaml"),
):
    """Run eval harness over coding questions (recorded mode)."""
    import yaml

    if not suite.exists():
        console.print(f"[red]Suite not found:[/red] {suite}")
        raise typer.Exit(1)

    questions = yaml.safe_load(suite.read_text())
    console.print(f"[bold]Eval harness[/bold] — {len(questions)} questions (recorded mode)")
    console.print("[dim]See evals/latest.md for results. Run with --recorded for keyless CI.[/dim]")

    results = []
    for q in questions:
        results.append({"id": q["id"], "status": "skipped", "note": "requires cassettes"})

    out_path = Path("evals/latest.md")
    lines = [
        "# Quorum Eval Results",
        "",
        f"Generated by `quorum eval`. Questions: {len(questions)}.",
        "",
        "## Metrics (honest)",
        "",
        "- Findings recall vs single-model baseline: not yet measured",
        "- Fast vs thorough delta: not yet measured",
        "- Disagreement rate: not yet measured",
        "- Judge parse-failure rate: not yet measured",
        "",
        "## Questions",
        "",
    ]
    for q in questions:
        lines.append(f"- **{q['id']}**: {q.get('question', '')[:80]}")
    out_path.write_text("\n".join(lines))
    console.print(f"[green]Wrote[/green] {out_path}")


app.command("eval")(eval_cmd)


@serve_app.callback(invoke_without_command=True)
def serve_main(
    ctx: typer.Context,
    host: Annotated[str, typer.Option()] = "0.0.0.0",
    port: Annotated[int, typer.Option()] = 8000,
    mcp: Annotated[bool, typer.Option("--mcp", help="Run MCP server instead")] = False,
):
    """Start the Quorum web server (REST + SSE + SPA)."""
    if ctx.invoked_subcommand:
        return
    if mcp:
        from quorum.mcp.server import run_mcp
        asyncio.run(run_mcp())
        return
    console.print(f"[bold]Quorum serve[/bold] → http://{host}:{port}")
    uvicorn.run("quorum.api.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()


def main() -> None:
    app()
