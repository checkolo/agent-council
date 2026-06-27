from pathlib import Path

import pytest

from quorum.council.decision import DecisionReport, parse_decision_report
from quorum.llm.cassettes import export_cassette, import_cassette
from quorum.storage.sqlite import Storage

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def storage(tmp_path):
    return Storage(tmp_path / "test.db")


def test_storage_self_test(storage):
    assert storage.self_test()


def test_storage_run_lifecycle(storage):
    run_id = storage.create_run("pr-review", "test input", "fast", 0.5)
    assert run_id
    run = storage.get_run(run_id)
    assert run["status"] == "pending"
    assert run["template"] == "pr-review"

    event_id = storage.add_event(run_id, "panel.done", {"content": "analysis"}, "architect")
    assert event_id > 0

    storage.update_run(run_id, status="complete", cost_usd=0.07, duration_ms=18000)
    run = storage.get_run(run_id)
    assert run["status"] == "complete"
    assert run["cost_usd"] == 0.07


def test_storage_list_runs(storage):
    storage.create_run("pr-review", "a", "fast")
    storage.create_run("architecture-review", "b", "thorough")
    runs = storage.list_runs(limit=10)
    assert len(runs) == 2


def test_cassette_roundtrip(tmp_path):
    run_data = {
        "run_id": "abc123",
        "template": "pr-review",
        "input": "sample diff",
        "decision_report": {
            "consensus": ["Use constant-time comparison"],
            "disagreements": [],
            "risks": [{"description": "Missing import for hmac", "severity": "major"}],
            "unknowns": [],
            "recommendation": {"action": "Add hmac import", "evidence": ["Security → hmac"]},
            "attribution": [{"role": "Security Reviewer", "idea": "Use hmac.compare_digest"}],
        },
    }
    path = export_cassette(run_data, tmp_path / "test")
    assert path.suffix == ".cassette"
    assert path.exists()

    loaded = import_cassette(path)
    assert loaded["run_id"] == "abc123"
    assert loaded["decision_report"]["consensus"][0] == "Use constant-time comparison"


def test_parse_decision_report_json():
    judge_output = """
## Consensus
- Members agree on security fix

```json
{
  "consensus": ["Members agree on security fix"],
  "disagreements": [],
  "risks": [{"description": "Weak hashing", "severity": "blocker"}],
  "unknowns": ["Deployment context unknown"],
  "recommendation": {"action": "Fix password hashing", "evidence": ["Security → pbkdf2"]},
  "attribution": [{"role": "Security Reviewer", "idea": "Use pbkdf2"}]
}
```
"""
    report = parse_decision_report(judge_output, task_id="test1", template="pr-review")
    assert len(report.consensus) == 1
    assert report.risks[0].severity == "blocker"
    assert report.recommendation.action == "Fix password hashing"


def test_parse_decision_report_markdown_fallback():
    judge_output = """
## Consensus
- Point one
- Point two

## Disagreements
- Topic A vs B

## Risks
- [major] Risk one

## Recommendation
- Do the thing
"""
    report = parse_decision_report(judge_output)
    assert len(report.consensus) == 2
    assert report.markdown_fallback is not None


def test_parse_decision_report_deliverable_section():
    judge_output = """
## Deliverable

# Magic in the Sky
### An Original Children's Song

**Verse 1**
Shine little star up in the sky

**Chorus**
Dream little dreamer, reach the sky!

## Consensus
- Theme is appropriate
"""
    report = parse_decision_report(judge_output)
    assert "Magic in the Sky" in report.deliverable
    assert "Verse 1" in report.deliverable
    assert "Chorus" in report.deliverable
    assert len(report.consensus) == 1


def test_decision_report_render():
    report = DecisionReport(
        consensus=["Fix auth"],
        recommendation={"action": "Add hmac", "evidence": ["Security → hmac"]},
    )
    from quorum.council.decision import render_markdown
    md = render_markdown(report)
    assert "## Consensus" in md
    assert "Fix auth" in md
