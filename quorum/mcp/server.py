from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from quorum.council.engine import RunContext, load_template, run_task
from quorum.llm.cassettes import export_cassette
from quorum.llm.openrouter import OpenRouterClient
from quorum.storage.sqlite import Storage

server = Server("quorum")
_active_runs: dict[str, dict[str, Any]] = {}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="quorum_review_start",
            description="Start an async council code review. Returns run_id for polling.",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Code diff or question to review"},
                    "template": {"type": "string", "default": "pr-review"},
                    "mode": {"type": "string", "enum": ["fast", "thorough"], "default": "fast"},
                    "max_cost": {"type": "number", "description": "Max cost in USD"},
                },
                "required": ["input"],
            },
        ),
        Tool(
            name="quorum_review_poll",
            description="Poll status of an async review run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                },
                "required": ["run_id"],
            },
        ),
        Tool(
            name="quorum_review_get",
            description="Get the Decision Report for a completed review run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                },
                "required": ["run_id"],
            },
        ),
    ]


async def _start_review(args: dict) -> str:
    storage = Storage()
    template_name = args.get("template", "pr-review")
    mode = args.get("mode", "fast")
    input_text = args["input"]
    max_cost = args.get("max_cost")

    template = load_template(template_name)
    run_id = storage.create_run(template_name, input_text, mode, max_cost)
    _active_runs[run_id] = {"status": "running", "storage": storage}

    async def _execute():
        client = OpenRouterClient()
        ctx = RunContext(
            run_id=run_id,
            template=template,
            input_text=input_text,
            mode=mode,  # type: ignore
            max_cost=max_cost or template.max_cost_usd,
        )
        try:
            report = await run_task(ctx, client, storage)
            run_data = {
                "run_id": run_id,
                "template": template_name,
                "input": input_text,
                "decision_report": report.model_dump(),
            }
            cassette_path = export_cassette(run_data, Path("cassettes") / run_id)
            _active_runs[run_id] = {
                "status": "complete",
                "report": report.model_dump(),
                "cassette_path": str(cassette_path),
            }
        except Exception as e:
            _active_runs[run_id] = {"status": "failed", "error": str(e)}

    asyncio.create_task(_execute())
    return json.dumps({"run_id": run_id, "status": "running"})


async def _poll_review(args: dict) -> str:
    run_id = args["run_id"]
    if run_id in _active_runs:
        info = _active_runs[run_id]
        return json.dumps({"run_id": run_id, "status": info.get("status", "unknown")})

    storage = Storage()
    run = storage.get_run(run_id)
    if not run:
        return json.dumps({"run_id": run_id, "status": "not_found"})
    return json.dumps({"run_id": run_id, "status": run["status"]})


async def _get_review(args: dict) -> str:
    run_id = args["run_id"]
    if run_id in _active_runs and _active_runs[run_id].get("status") == "complete":
        info = _active_runs[run_id]
        return json.dumps({
            "run_id": run_id,
            "status": "complete",
            "decision_report": info.get("report"),
            "cassette_path": info.get("cassette_path"),
        })

    storage = Storage()
    run = storage.get_run(run_id)
    if not run:
        return json.dumps({"error": "Run not found"})
    if run["status"] != "complete":
        return json.dumps({"run_id": run_id, "status": run["status"]})
    return json.dumps({
        "run_id": run_id,
        "status": "complete",
        "decision_report": run.get("decision_report"),
    })


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "quorum_review_start":
        result = await _start_review(arguments)
    elif name == "quorum_review_poll":
        result = await _poll_review(arguments)
    elif name == "quorum_review_get":
        result = await _get_review(arguments)
    else:
        result = json.dumps({"error": f"Unknown tool: {name}"})
    return [TextContent(type="text", text=result)]


async def run_mcp() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
