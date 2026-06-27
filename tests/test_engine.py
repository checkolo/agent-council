from pathlib import Path

import pytest

from quorum.council.engine import list_templates, load_template
from quorum.council.roles import ROLES, get_role


def test_roles_exist():
    assert "architect" in ROLES
    assert "security" in ROLES
    assert "performance" in ROLES
    assert "qa" in ROLES


def test_get_role():
    role = get_role("architect")
    assert role.display_name == "Architect"


def test_get_role_invalid():
    with pytest.raises(ValueError):
        get_role("nonexistent")


def test_list_templates():
    templates = list_templates(Path("templates"))
    names = [t.name for t in templates]
    assert "pr-review" in names
    assert "architecture-review" in names


def test_load_pr_review_template():
    t = load_template("pr-review", Path("templates"))
    assert t.name == "pr-review"
    assert len(t.roles) == 4
    assert "architect" in t.roles
