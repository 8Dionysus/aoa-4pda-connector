from __future__ import annotations

from pathlib import Path

from scripts.release_check import (
    EXPECTED_STATS_RELEASE_REVISION,
    exact_published_stats_pin,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_release_law_requires_exact_published_stats_commit():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")

    ok, detail = exact_published_stats_pin(workflow, releasing)

    assert ok, detail
    assert EXPECTED_STATS_RELEASE_REVISION in workflow


def test_release_law_rejects_ancestor_only_stats_pin():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    ancestor_workflow = workflow.replace(EXPECTED_STATS_RELEASE_REVISION, "ae87240bd5f1b64769fcf39b4eae67363cee9f38", 1)

    ok, detail = exact_published_stats_pin(ancestor_workflow, releasing)

    assert not ok
    assert "ancestor-only" in detail
