from __future__ import annotations

from pathlib import Path

from scripts.release_check import (
    EXPECTED_KAG_RELEASE_REVISION,
    EXPECTED_STATS_RELEASE_REVISION,
    exact_published_kag_pin,
    exact_published_stats_pin,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_release_law_requires_exact_published_stats_commit():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")

    ok, detail = exact_published_stats_pin(workflow, releasing)

    assert ok, detail
    assert EXPECTED_STATS_RELEASE_REVISION in workflow


def test_release_law_requires_exact_published_kag_commit():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")

    ok, detail = exact_published_kag_pin(workflow, releasing)

    assert ok, detail
    assert EXPECTED_KAG_RELEASE_REVISION in workflow


def test_release_law_rejects_ancestor_only_kag_action_pin():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    stale_workflow = workflow.replace(EXPECTED_KAG_RELEASE_REVISION, "6a79e62c7d20b6b11406dee78f409ada4a51bb3f", 1)

    ok, detail = exact_published_kag_pin(stale_workflow, releasing)

    assert not ok
    assert "ancestor-only" in detail


def test_release_law_rejects_ancestor_only_stats_pin():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    ancestor_workflow = workflow.replace(EXPECTED_STATS_RELEASE_REVISION, "ae87240bd5f1b64769fcf39b4eae67363cee9f38", 1)

    ok, detail = exact_published_stats_pin(ancestor_workflow, releasing)

    assert not ok
    assert "ancestor-only" in detail


def test_release_law_rejects_previous_published_stats_pin():
    workflow = (REPO_ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    stale_workflow = workflow.replace(
        EXPECTED_STATS_RELEASE_REVISION,
        "339ecb2db22ac4552fa88756b650896ebbff5b56",
        1,
    )

    ok, detail = exact_published_stats_pin(stale_workflow, releasing)

    assert not ok
    assert "not the exact peeled" in detail
