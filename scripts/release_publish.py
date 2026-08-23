#!/usr/bin/env python3
"""Dry-run and publish the connector's owner-local source-only release."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REMOTE = "https://github.com/8Dionysus/aoa-4pda-connector.git"
GITHUB_REPO = "8Dionysus/aoa-4pda-connector"


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        list(args),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"{' '.join(args)} failed: {detail}")
    return proc


def release_body(repo: Path, version: str) -> str:
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        raise RuntimeError(f"CHANGELOG.md has no dated [{version}] section")
    body = text[match.end() :]
    next_heading = re.search(r"^## \[", body, flags=re.MULTILINE)
    if next_heading:
        body = body[: next_heading.start()]
    body = body.strip()
    if not body:
        raise RuntimeError("release section is empty")
    return body + "\n"


def remote_release_exists(repo: Path, tag: str) -> bool:
    proc = run(repo, "gh", "api", f"repos/{GITHUB_REPO}/releases/tags/{tag}", check=False)
    return proc.returncode == 0


def remote_tag_exists(repo: Path, tag: str) -> bool:
    proc = run(repo, "git", "ls-remote", REMOTE, f"refs/tags/{tag}*", check=False)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo_root.resolve()
    if args.tag != f"v{args.version}":
        raise SystemExit("--tag must be v<--version>")

    status = run(repo, "git", "status", "--porcelain").stdout.strip()
    if status:
        raise SystemExit("release publisher requires a clean worktree")
    branch = run(repo, "git", "branch", "--show-current").stdout.strip()
    if branch != "main":
        raise SystemExit(f"release publisher requires branch main, observed {branch or 'detached'}")
    head = run(repo, "git", "rev-parse", "HEAD").stdout.strip()
    origin_main = run(repo, "git", "rev-parse", "refs/remotes/origin/main").stdout.strip()
    if head != origin_main:
        raise SystemExit(f"HEAD {head} is not local origin/main {origin_main}")

    body = release_body(repo, args.version)
    local_tag = run(repo, "git", "rev-parse", f"{args.tag}^{{}}", check=False)
    if local_tag.returncode == 0 and local_tag.stdout.strip() != head:
        raise SystemExit(f"existing local {args.tag} does not point to HEAD")
    if remote_tag_exists(repo, args.tag):
        raise SystemExit(f"remote tag {args.tag} already exists; refusing overwrite")
    if remote_release_exists(repo, args.tag):
        raise SystemExit(f"remote release {args.tag} already exists; refusing overwrite")

    plan = {
        "schema": "aoa_4pda_release_publish_plan_v1",
        "mode": "dry-run" if args.dry_run else "confirm",
        "repo": GITHUB_REPO,
        "version": args.version,
        "tag": args.tag,
        "head": head,
        "branch": branch,
        "source_only": True,
        "assets": [],
        "release_body_sha256": __import__("hashlib").sha256(body.encode()).hexdigest(),
        "remote_tag_absent": True,
        "remote_release_absent": True,
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if local_tag.returncode != 0:
        run(repo, "git", "tag", "-a", args.tag, "-m", f"aoa-4pda-connector {args.tag}", head)
    run(repo, "git", "push", REMOTE, f"refs/tags/{args.tag}")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md") as notes:
        notes.write(body)
        notes.flush()
        run(
            repo,
            "gh",
            "release",
            "create",
            args.tag,
            "--repo",
            GITHUB_REPO,
            "--title",
            f"aoa-4pda-connector {args.tag}",
            "--notes-file",
            notes.name,
            "--verify-tag",
        )

    release = json.loads(run(repo, "gh", "api", f"repos/{GITHUB_REPO}/releases/tags/{args.tag}").stdout)
    if release.get("tag_name") != args.tag or release.get("draft") or release.get("prerelease"):
        raise RuntimeError("postpublish release identity/status mismatch")
    if release.get("body", "").strip() != body.strip():
        raise RuntimeError("postpublish release body differs from canonical CHANGELOG section")
    if release.get("assets"):
        raise RuntimeError("source-only release unexpectedly has assets")
    latest = json.loads(run(repo, "gh", "api", f"repos/{GITHUB_REPO}/releases/latest").stdout)
    if latest.get("tag_name") != args.tag:
        raise RuntimeError(f"latest marker is {latest.get('tag_name')!r}, expected {args.tag}")
    remote_refs = run(repo, "git", "ls-remote", REMOTE, f"refs/tags/{args.tag}*").stdout.splitlines()
    peeled = next((line.split()[0] for line in remote_refs if line.endswith(f"refs/tags/{args.tag}^{{}}")), "")
    if peeled != head:
        raise RuntimeError(f"remote peeled tag commit {peeled!r} differs from {head}")
    plan.update(
        {
            "published": True,
            "release_url": release.get("html_url"),
            "remote_tag_commit": peeled,
            "latest_tag": latest.get("tag_name"),
            "postpublish_passed": True,
        }
    )
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"release_publish: {exc}", file=sys.stderr)
        raise SystemExit(1)
