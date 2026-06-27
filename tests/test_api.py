import pytest
from fastapi.testclient import TestClient

from quorum.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "has_api_key" in data
    assert isinstance(data["has_api_key"], bool)


def test_judge_models(client):
    resp = client.get("/api/models")
    assert resp.status_code == 200
    models = resp.json()["judge_models"]
    assert "minimax/minimax-m3:exacto" in models
    assert "anthropic/claude-sonnet-4" in models


def test_templates(client):
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    names = [t["name"] for t in data]
    assert "pr-review" in names
    assert "song-writer" in names
    pr = next(t for t in data if t["name"] == "pr-review")
    assert "role_details" in pr
    assert len(pr["role_details"]) >= 4
    assert "display_name" in pr["role_details"][0]
    assert "suggested_models" in pr["role_details"][0]
    assert "minimax/minimax-m3:exacto" in pr["role_details"][0]["suggested_models"]
    assert "deepseek/deepseek-v4-flash" in pr["role_details"][0]["suggested_models"]
    assert "outcomes" in pr
    assert "default_outcome" in pr
    assert len(pr["outcomes"]) >= 2


def test_sample_diff(client):
    resp = client.get("/api/demo/sample-diff")
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "filename" in data
    assert "diff --git" in data["content"]


def test_sample_brief(client):
    resp = client.get("/api/demo/sample-brief")
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "song-brief.txt"
    assert "song" in data["content"].lower() or "space" in data["content"].lower()


def test_demo_samples(client):
    resp = client.get("/api/demo/samples")
    assert resp.status_code == 200
    samples = resp.json()["samples"]
    assert "song-writer" in samples
    assert "pr-review" in samples


def test_sample_cassette(client):
    resp = client.get("/api/cassettes/samples/demo-auth")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == "demo-auth"


def test_create_run_with_roles_subset(client):
    resp = client.post("/api/runs", json={
        "template": "pr-review",
        "input": "subset test",
        "mode": "fast",
        "recorded": True,
        "roles": ["architect", "security"],
    })
    assert resp.status_code == 200


def test_create_run_invalid_roles(client):
    resp = client.post("/api/runs", json={
        "template": "pr-review",
        "input": "bad roles",
        "roles": ["nonexistent"],
    })
    assert resp.status_code == 400


def test_create_run_recorded(client):
    resp = client.post("/api/runs", json={
        "template": "pr-review",
        "input": "test input for review",
        "mode": "fast",
        "recorded": True,
        "max_cost": 0.50,
    })
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    assert run_id

    get_resp = client.get(f"/api/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == run_id


def test_export_run(client):
    create = client.post("/api/runs", json={
        "template": "pr-review",
        "input": "export test",
        "mode": "fast",
        "recorded": True,
    })
    run_id = create.json()["run_id"]

    export_resp = client.get(f"/api/runs/{run_id}/export")
    assert export_resp.status_code == 200
    assert export_resp.headers["content-type"] == "application/zip"
    assert len(export_resp.content) > 0


def test_list_runs(client):
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    assert "runs" in resp.json()


def test_cassette_view(client):
    cassette_path = "cassettes/samples/demo-auth.cassette"
    with open(cassette_path, "rb") as f:
        resp = client.post(
            "/api/cassettes/view",
            files={"file": ("demo-auth.cassette", f, "application/zip")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == "demo-auth"


def test_spa_client_route_refresh(client):
    resp = client.get("/runs/example-id")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "<!doctype html>" in resp.text.lower()


def test_spa_missing_asset_stays_404(client):
    resp = client.get("/assets/does-not-exist.js")
    assert resp.status_code == 404
