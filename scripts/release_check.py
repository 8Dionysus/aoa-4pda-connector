#!/usr/bin/env python3
"""Run the deterministic owner-local release-surface preflight."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "Summary",
    "Added",
    "Changed",
    "Fixed",
    "Deprecated",
    "Removed",
    "Security",
    "Validation",
    "Notes",
    "First-Parent Reconciliation",
)

# These are the current published provider identities resolved from the live
# GitHub Releases/tags. A future provider release must update this owner-local
# law and its corresponding workflow pin together.
EXPECTED_KAG_RELEASE_TAG = "v0.5.2"
EXPECTED_KAG_RELEASE_REVISION = "8136d3eb629da28cea1206d13a8f1df52ee14739"
EXPECTED_KAG_RELEASE_TAG_OBJECT = "251846823f49d18b06c32374b3434e6e11002e96"
EXPECTED_STATS_RELEASE_TAG = "v0.2.2"
EXPECTED_STATS_RELEASE_REVISION = "f119805cda69b3edeb2a4c5e407368d70e68650d"
EXPECTED_STATS_RELEASE_TAG_OBJECT = "119f434918e8218e43e977b2edec3e4feab6b493"


def exact_published_kag_pin(workflow_text: str, releasing_text: str) -> tuple[bool, str]:
    """Require the direct KAG action to equal the published release commit."""

    match = re.search(
        r"^\s+uses:\s+8Dionysus/aoa-kag/\.github/actions/repo-local-kag-index@([0-9a-f]{40})\s*$",
        workflow_text,
        flags=re.MULTILINE,
    )
    if match is None:
        return False, "workflow has no pinned aoa-kag repo-local action"
    observed = match.group(1)
    if observed != EXPECTED_KAG_RELEASE_REVISION:
        return (
            False,
            f"aoa-kag action {observed} is not the exact published {EXPECTED_KAG_RELEASE_TAG} "
            f"commit {EXPECTED_KAG_RELEASE_REVISION}; ancestor-only pins are invalid",
        )
    required = (
        f"`{EXPECTED_KAG_RELEASE_TAG}` tag object `{EXPECTED_KAG_RELEASE_TAG_OBJECT}` peels to "
        f"`{EXPECTED_KAG_RELEASE_REVISION}`",
        f"action `{EXPECTED_KAG_RELEASE_REVISION}`",
        f"owner-family/generated pin `{EXPECTED_KAG_RELEASE_REVISION}`",
    )
    missing = [needle for needle in required if needle not in releasing_text]
    if missing:
        return False, "docs/RELEASING.md is missing exact KAG identity: " + ", ".join(missing)
    return True, f"aoa-kag action equals published {EXPECTED_KAG_RELEASE_TAG} commit"


def exact_published_stats_pin(workflow_text: str, releasing_text: str) -> tuple[bool, str]:
    """Require the direct stats checkout to equal the published tag peel."""

    match = re.search(
        r"^\s+AOA_STATS_REVISION:\s*([0-9a-f]{40})\s*$",
        workflow_text,
        flags=re.MULTILINE,
    )
    if match is None:
        return False, "workflow has no 40-hex AOA_STATS_REVISION"
    observed = match.group(1)
    if observed != EXPECTED_STATS_RELEASE_REVISION:
        return (
            False,
            f"AOA_STATS_REVISION {observed} is not the exact peeled {EXPECTED_STATS_RELEASE_TAG} commit "
            f"{EXPECTED_STATS_RELEASE_REVISION}; ancestor-only pins are invalid",
        )
    required = (
        f"`{EXPECTED_STATS_RELEASE_TAG}`",
        f"tag object `{EXPECTED_STATS_RELEASE_TAG_OBJECT}` peels to `{EXPECTED_STATS_RELEASE_REVISION}`",
        f"AOA_STATS_REVISION={EXPECTED_STATS_RELEASE_REVISION}",
        "the workflow checkout must equal the published tag's peeled commit",
    )
    missing = [needle for needle in required if needle not in releasing_text]
    if missing:
        return False, "docs/RELEASING.md is missing exact stats identity: " + ", ".join(missing)
    return True, f"AOA_STATS_REVISION equals published {EXPECTED_STATS_RELEASE_TAG} peeled commit"


def fail(checks: list[dict[str, object]], name: str, detail: str) -> None:
    checks.append({"name": name, "status": "fail", "detail": detail})


def pass_check(checks: list[dict[str, object]], name: str, detail: str) -> None:
    checks.append({"name": name, "status": "pass", "detail": detail})


def section_body(changelog: str, version: str) -> str | None:
    match = re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*$",
        changelog,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    tail = changelog[match.end() :]
    next_heading = re.search(r"^## \[", tail, flags=re.MULTILINE)
    return tail[: next_heading.start()] if next_heading else tail


def git(repo: Path, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--expected-branch", default="")
    args = parser.parse_args(argv)
    repo = args.repo_root.resolve()
    version = args.version
    checks: list[dict[str, object]] = []

    pyproject = (repo / "pyproject.toml").read_text(encoding="utf-8")
    init_text = (repo / "src" / "aoa_4pda_connector" / "__init__.py").read_text(encoding="utf-8")
    manifest_text = (repo / "connector" / "manifests" / "connector_manifest.yaml").read_text(encoding="utf-8")
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (repo / "README.md").read_text(encoding="utf-8")
    releasing = (repo / "docs" / "RELEASING.md").read_text(encoding="utf-8")
    workflow = (repo / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")

    expected = f'version = "{version}"'
    if expected in pyproject:
        pass_check(checks, "pyproject-version", version)
    else:
        fail(checks, "pyproject-version", f"missing {expected!r}")

    if re.search(rf'^__version__\s*=\s*["\']{re.escape(version)}["\']$', init_text, re.MULTILINE):
        pass_check(checks, "python-version", version)
    else:
        fail(checks, "python-version", f"__version__ is not {version}")

    if re.search(rf"^  version: {re.escape(version)}$", manifest_text, re.MULTILINE):
        pass_check(checks, "manifest-version", version)
    else:
        fail(checks, "manifest-version", f"manifest release.version is not {version}")

    release = section_body(changelog, version)
    if release is None:
        fail(checks, "dated-changelog-heading", f"missing dated [{version}] heading")
    else:
        missing = [name for name in REQUIRED_SECTIONS if f"### {name}" not in release]
        if missing:
            fail(checks, "release-sections", "missing: " + ", ".join(missing))
        else:
            pass_check(checks, "release-sections", "all human-first and reconciliation sections present")

    if "## [Unreleased]" in changelog and "_No unreleased changes._" in changelog:
        pass_check(checks, "unreleased-marker", "empty explicit Unreleased section")
    else:
        fail(checks, "unreleased-marker", "expected empty ## [Unreleased] section")

    marker = f"Current release: v{version}"
    if marker in readme:
        pass_check(checks, "readme-marker", marker)
    else:
        fail(checks, "readme-marker", f"missing {marker!r}")

    for needle in ("source-only", "aoa-sdk"):
        if needle in releasing:
            pass_check(checks, f"releasing-{needle}", "owner-local law references required boundary")
        else:
            fail(checks, f"releasing-{needle}", f"missing {needle!r} in docs/RELEASING.md")

    kag_pin_ok, kag_pin_detail = exact_published_kag_pin(workflow, releasing)
    if kag_pin_ok:
        pass_check(checks, "published-kag-exact-pin", kag_pin_detail)
    else:
        fail(checks, "published-kag-exact-pin", kag_pin_detail)

    stats_pin_ok, stats_pin_detail = exact_published_stats_pin(workflow, releasing)
    if stats_pin_ok:
        pass_check(checks, "published-stats-exact-pin", stats_pin_detail)
    else:
        fail(checks, "published-stats-exact-pin", stats_pin_detail)

    code, branch, err = git(repo, "branch", "--show-current")
    if code == 0 and branch:
        if args.expected_branch and branch != args.expected_branch:
            fail(checks, "branch", f"expected {args.expected_branch}, observed {branch}")
        else:
            pass_check(checks, "branch", branch)
    elif args.expected_branch:
        fail(checks, "branch", err or "detached HEAD")

    if args.require_clean:
        code, status, err = git(repo, "status", "--porcelain")
        if code == 0 and not status:
            pass_check(checks, "clean-worktree", "no tracked or untracked changes")
        else:
            fail(checks, "clean-worktree", status or err or "git status failed")

    passed = sum(check["status"] == "pass" for check in checks)
    failed = sum(check["status"] == "fail" for check in checks)
    payload = {
        "schema": "aoa_4pda_release_check_v1",
        "status": "ok" if failed == 0 else "error",
        "repo": str(repo),
        "version": version,
        "summary": {"passed": passed, "failed": failed},
        "checks": checks,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
