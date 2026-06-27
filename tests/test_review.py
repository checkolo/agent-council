
from quorum.council.review import anonymize_outputs, parse_peer_review


def test_anonymize_outputs():
    outputs = [
        {"role": "Architect", "content": "Good structure"},
        {"role": "Security Reviewer", "content": "Fix auth"},
        {"role": "QA Engineer", "content": "Add tests"},
    ]
    text, aliases = anonymize_outputs(outputs, exclude_role="Architect")
    assert "Reviewer A" in text
    assert "Reviewer B" in text
    assert "Architect" not in text
    assert len(aliases) == 2


def test_parse_peer_review_json():
    content = """
Here is my review:

```json
{
  "rankings": [{"reviewer": "A", "rank": 1, "reason": "Critical security issue"}],
  "disagreements": [{"topic": "severity", "positions": {"A": "blocker", "B": "minor"}}],
  "missing": ["performance analysis"]
}
```
"""
    parsed = parse_peer_review(content)
    assert parsed is not None
    assert len(parsed["rankings"]) == 1
    assert parsed["rankings"][0]["reviewer"] == "A"


def test_parse_peer_review_invalid():
    assert parse_peer_review("no json here") is None
