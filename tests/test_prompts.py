from quorum.council.prompts import JUDGE_PROMPT, PANEL_MEMBER_PROMPT, PEER_REVIEWER_PROMPT, panel_prompt


def test_panel_prompt_contains_role():
    prompt = panel_prompt("Security Reviewer", "threat model and auth", "Review this diff")
    assert "Security Reviewer" in prompt
    assert "Review this diff" in prompt
    assert "threat model and auth" in prompt
    assert "## Findings" in prompt


def test_panel_member_prompt_structure():
    assert "{role}" in PANEL_MEMBER_PROMPT or "Security Reviewer" in PANEL_MEMBER_PROMPT
    assert "## Evidence" in PANEL_MEMBER_PROMPT
    assert "## Confidence" in PANEL_MEMBER_PROMPT


def test_peer_reviewer_prompt_structure():
    assert "rankings" in PEER_REVIEWER_PROMPT
    assert "disagreements" in PEER_REVIEWER_PROMPT
    formatted = PEER_REVIEWER_PROMPT.format(n=3)
    assert "3 other council members" in formatted


def test_judge_prompt_structure():
    assert "## Deliverable" in JUDGE_PROMPT
    assert "## Consensus" in JUDGE_PROMPT
    assert "## Disagreements" in JUDGE_PROMPT
    assert "## Attribution" in JUDGE_PROMPT
    assert "deliverable" in JUDGE_PROMPT  # JSON schema hint
