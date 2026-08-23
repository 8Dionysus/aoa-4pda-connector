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

# This is the current published aoa-stats provider identity resolved from the
# live v0.2.1 GitHub Release/tag. A future provider release must update this
# owner-local law and its corresponding workflow pin together.
EXPECTED_STATS_RELEASE_TAG = "v0.2.1"
EXPECTED_STATS_RELEASE_REVISION = "339ecb2db22ac4552fa88756b650896ebbff5b56"


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
    if (
        f"AOA_STATS_REVISION={EXPECTED_STATS_RELEASE_REVISION}" not in releasing_text
        or "the workflow checkout must equal the published tag's peeled commit" not in releasing_text
    ):
        return False, "docs/RELEASING.md does not state the exact published stats identity"
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

    for needle in ("v0.5.0", "v0.2.1", "source-only", "aoa-sdk"):
        if needle in releasing:
            pass_check(checks, f"releasing-{needle}", "owner-local law references required boundary")
        else:
            fail(checks, f"releasing-{needle}", f"missing {needle!r} in docs/RELEASING.md")

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
