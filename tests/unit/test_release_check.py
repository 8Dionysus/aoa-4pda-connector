from __future__ import annotations

from pathlib import Path

from scripts.release_check import (
    EXPECTED_KAG_RELEASE_REVISION,
    EXPECTED_STATS_RELEASE_REVISION,
    exact_active_stats_declarations,
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


def test_active_surfaces_require_exact_published_stats_identity():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    decision = (
        REPO_ROOT / "docs/decisions/AOA-4PDA-D-0039-exact-published-provider-identity.md"
    ).read_text(encoding="utf-8")
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    ok, detail = exact_active_stats_declarations(
        readme, roadmap, releasing, decision, changelog
    )

    assert ok, detail


def test_dated_release_body_rejects_superseded_stats_identity():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    decision = (
        REPO_ROOT / "docs/decisions/AOA-4PDA-D-0039-exact-published-provider-identity.md"
    ).read_text(encoding="utf-8")
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    stale_changelog = changelog.replace(
        "direct `aoa-stats@v0.2.0` tag object `a63dd6f95c6f0c87a371720885c2d90a1baa3436` peels to `88ff38b1b38eef939f2c5b4541cbe8363a05fc8d`",
        "direct `aoa-stats@v0.2.2` tag object `119f434918e8218e43e977b2edec3e4feab6b493` peels to `f119805cda69b3edeb2a4c5e407368d70e68650d`",
        1,
    )

    ok, detail = exact_active_stats_declarations(
        readme, roadmap, releasing, decision, stale_changelog
    )

    assert not ok
    assert "CHANGELOG.md [0.1.0]" in detail


def test_dated_release_body_rejects_historical_stats_pointer_even_with_current_pin():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    releasing = (REPO_ROOT / "docs/RELEASING.md").read_text(encoding="utf-8")
    decision = (
        REPO_ROOT / "docs/decisions/AOA-4PDA-D-0039-exact-published-provider-identity.md"
    ).read_text(encoding="utf-8")
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    contaminated_changelog = changelog.replace(
        "Historical carrier bodies, tagged changelog snapshots, and the pre-mutation conservation evidence retain their original provider records outside this canonical release body.",
        "The canonical body also mentions aoa-stats@v0.2.2 for historical context.",
        1,
    )

    ok, detail = exact_active_stats_declarations(
        readme, roadmap, releasing, decision, contaminated_changelog
    )

    assert not ok
    assert "superseded aoa-stats identity" in detail


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
