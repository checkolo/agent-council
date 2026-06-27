from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

from dataclasses import replace

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from quorum import __version__
from quorum.api.events import (
    make_event_callback,
    replay_events_from_storage,
    subscribe,
    unsubscribe,
)
from quorum.council.engine import (
    CostCapExceeded,
    RunContext,
    list_templates,
    load_template,
    run_task,
)
from quorum.council.models import JUDGE_MODELS
from quorum.council.roles import get_role
from quorum.llm.cassettes import export_cassette, import_cassette
from quorum.llm.openrouter import OpenRouterClient
from quorum.storage.sqlite import Storage

app = FastAPI(title="Quorum", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage


class CreateRunRequest(BaseModel):
    template: str
    input: str
    mode: str = "fast"
    max_cost: float | None = None
    model_overrides: dict[str, str] | None = None
    roles: list[str] | None = None
    recorded: bool = False
    desired_outcome: str | None = None
    judge_max_tokens: int | None = None


class CreateRunResponse(BaseModel):
    run_id: str


def _has_api_key() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _role_details(role_keys: list[str]) -> list[dict]:
    details = []
    for key in role_keys:
        role = get_role(key)
        details.append({
            "key": key,
            "display_name": role.display_name,
            "suggested_models": role.suggested_models,
        })
    return details


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": __version__, "has_api_key": _has_api_key()}


@app.get("/api/models")
async def get_models():
    return {"judge_models": JUDGE_MODELS}


@app.get("/api/templates")
async def get_templates():
    templates = list_templates()
    return [
        {
            "name": t.name,
            "description": t.description,
            "roles": t.roles,
            "role_details": _role_details(t.roles),
            "judge_model": t.judge_model,
            "mode": t.mode,
            "max_cost_usd": t.max_cost_usd,
            "default_outcome": t.default_outcome,
            "outcomes": [
                {
                    "id": o.id,
                    "label": o.label,
                    "description": o.description,
                }
                for o in t.outcomes
            ],
        }
        for t in templates
    ]


@app.get("/api/demo/sample-diff")
async def get_sample_diff():
    path = Path("tests/fixtures/sample.diff")
    if not path.exists():
        raise HTTPException(404, "Sample diff not found")
    return {"content": path.read_text(), "filename": "sample.diff"}


@app.get("/api/demo/sample-brief")
async def get_sample_brief():
    path = Path("tests/fixtures/song-brief.txt")
    if not path.exists():
        raise HTTPException(404, "Sample brief not found")
    return {"content": path.read_text(), "filename": "song-brief.txt"}


@app.get("/api/demo/samples")
async def get_demo_samples():
    """Sample inputs keyed by template name for the composer UI."""
    diff_path = Path("tests/fixtures/sample.diff")
    brief_path = Path("tests/fixtures/song-brief.txt")
    diff = diff_path.read_text() if diff_path.exists() else ""
    brief = brief_path.read_text() if brief_path.exists() else ""
    return {
        "samples": {
            "pr-review": {"filename": "sample.diff", "content": diff},
            "architecture-review": {"filename": "sample.diff", "content": diff},
            "song-writer": {"filename": "song-brief.txt", "content": brief},
        }
    }


@app.get("/api/runs/{run_id}/export")
async def export_run(run_id: str):
    storage = get_storage()
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")
    run_data = {
        "run_id": run_id,
        "template": run["template"],
        "input": run["input_text"],
        "mode": run["mode"],
        "decision_report": run.get("decision_report"),
        "events": storage.get_events(run_id),
    }
    with tempfile.NamedTemporaryFile(suffix=".cassette", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    export_cassette(run_data, tmp_path)
    return FileResponse(
        path=tmp_path,
        filename=f"{run_id}.cassette",
        media_type="application/zip",
    )


@app.get("/api/cassettes/samples/{name}")
async def get_sample_cassette(name: str):
    allowed = {"demo-auth", "demo-arch"}
    if name not in allowed:
        raise HTTPException(404, f"Sample not found: {name}")
    path = Path("cassettes/samples") / f"{name}.cassette"
    if not path.exists():
        raise HTTPException(404, f"Sample not found: {name}")
    return import_cassette(path)


def _apply_role_subset(template, roles: list[str] | None):
    if roles is None:
        return template
    valid = set(template.roles)
    invalid = [r for r in roles if r not in valid]
    if invalid:
        raise HTTPException(400, f"Invalid roles for template: {invalid}")
    if len(roles) < 1:
        raise HTTPException(400, "At least one council role is required")
    return replace(template, roles=roles)


async def _execute_run(run_id: str, req: CreateRunRequest) -> None:
    storage = get_storage()
    try:
        template = _apply_role_subset(load_template(req.template), req.roles)
        client = OpenRouterClient(recorded=req.recorded)
        ctx = RunContext(
            run_id=run_id,
            template=template,
            input_text=req.input,
            mode=req.mode,  # type: ignore
            max_cost=req.max_cost,
            model_overrides=req.model_overrides or {},
            desired_outcome=req.desired_outcome,
            judge_max_tokens=req.judge_max_tokens,
            on_event=make_event_callback(run_id),
        )
        storage.update_run(run_id, status="running")
        await run_task(ctx, client, storage)
    except CostCapExceeded as e:
        storage.update_run(run_id, status="failed", error=str(e))
        make_event_callback(run_id)("run.done", {"status": "failed", "error": str(e)})
        storage.add_event(run_id, "run.done", {"status": "failed", "error": str(e)})
    except Exception as e:
        storage.update_run(run_id, status="failed", error=str(e))
        make_event_callback(run_id)("run.done", {"status": "failed", "error": str(e)})
        storage.add_event(run_id, "run.done", {"status": "failed", "error": str(e)})


@app.post("/api/runs", response_model=CreateRunResponse)
async def create_run(req: CreateRunRequest, background_tasks: BackgroundTasks):
    storage = get_storage()
    try:
        template = _apply_role_subset(load_template(req.template), req.roles)
    except FileNotFoundError:
        raise HTTPException(404, f"Template not found: {req.template}")
    run_id = storage.create_run(req.template, req.input, req.mode, req.max_cost)
    background_tasks.add_task(_execute_run, run_id, req)
    return CreateRunResponse(run_id=run_id)


@app.get("/api/runs")
async def get_runs(
    limit: int = Query(20, le=100),
    offset: int = 0,
    template: str | None = None,
    status: str | None = None,
):
    storage = get_storage()
    runs = storage.list_runs(limit, offset, template, status)
    return {"runs": runs, "limit": limit, "offset": offset}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    storage = get_storage()
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")
    return run


@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str, after: int = Query(0)):
    storage = get_storage()
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    async def event_generator():
        # Replay persisted events first
        events = await replay_events_from_storage(storage, run_id, after)
        for ev in events:
            yield {
                "event": ev["event_type"],
                "id": str(ev["id"]),
                "data": json.dumps(ev["payload"]),
            }

        if run.get("status") in ("complete", "failed"):
            return

        q = subscribe(run_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield {
                        "event": event["type"],
                        "data": json.dumps(event["data"]),
                    }
                    if event["type"] == "run.done":
                        break
                except TimeoutError:
                    yield {"event": "ping", "data": "{}"}
        finally:
            unsubscribe(run_id, q)

    return EventSourceResponse(event_generator())


@app.post("/api/cassettes/view")
async def view_cassette(file: UploadFile = File(...)):
    content = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".cassette", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        run_data = import_cassette(tmp_path)
        return run_data
    except Exception as e:
        raise HTTPException(400, f"Invalid cassette: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)


class SPAStaticFiles(StaticFiles):
    """StaticFiles with SPA fallback: unknown routes serve index.html."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404 or not self.html:
                raise
            # Missing static assets (e.g. *.js) should stay 404.
            if "." in path.rsplit("/", 1)[-1]:
                raise
            return await super().get_response("index.html", scope)


def mount_spa(web_dir: Path | None = None) -> None:
    """Mount built SPA at root (call after all API routes are registered)."""
    directory = web_dir or Path(__file__).parent.parent / "web"
    if directory.exists() and (directory / "index.html").exists():
        app.mount("/", SPAStaticFiles(directory=str(directory), html=True), name="spa")


mount_spa()
