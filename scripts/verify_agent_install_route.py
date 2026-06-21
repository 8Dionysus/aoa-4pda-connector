#!/usr/bin/env python3
"""Verify the documented no-network agent install route from a fresh copy."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence


SCHEMA = "aoa_4pda_agent_install_route_verify_v1"
DEFAULT_QUERY = "bootloop recovery.img camellia"
ALLOWED_CONNECTOR_STATE_FILES = {
    ".connector-state/AGENTS.md",
    ".connector-state/README.md",
    ".connector-state/artifacts/.gitkeep",
    ".connector-state/cache/.gitkeep",
    ".connector-state/data/.gitkeep",
}
IGNORED_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
IGNORED_SUFFIXES = (".egg-info", ".pyc", ".pyo")


@dataclass(frozen=True)
class Step:
    step_id: str
    command: tuple[str, ...]
    cwd: Path
    expect_json: bool = False
    connector_runtime: bool = True


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    source_root = args.source.resolve()
    if args.plan_only:
        print(
            json.dumps(
                _plan_payload(source_root, args),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    work_root = _work_root(args.work_root)
    temp_root = Path(tempfile.mkdtemp(prefix="aoa-4pda-agent-install-", dir=work_root))
    copy_root = temp_root / "repo"
    storage_root = temp_root / "storage"
    report: dict[str, object] = {
        "schema": SCHEMA,
        "status": "running",
        "created_at": _now(),
        "source_root": str(source_root),
        "work_root": str(temp_root),
        "copy_root": str(copy_root),
        "storage_root": str(storage_root),
        "package_install_may_use_network": not args.skip_install,
        "connector_route_network_touched": False,
        "keep": bool(args.keep),
        "steps": [],
    }
    try:
        _copy_source_tree(source_root, copy_root)
        storage_roots = {
            "CONNECTOR_DATA_ROOT": str(storage_root / "data"),
            "CONNECTOR_CACHE_ROOT": str(storage_root / "cache"),
            "CONNECTOR_ARTIFACT_ROOT": str(storage_root / "artifacts"),
        }
        env = os.environ.copy()
        env.update(storage_roots)
        env.pop("PYTHONPATH", None)
        report["storage_roots"] = storage_roots
        report["copied_repo_state"] = _repo_state(copy_root)

        python_bin = Path(args.python).resolve()
        if not args.skip_install:
            venv_dir = temp_root / ".venv"
            _record_step(
                report,
                Step("create_venv", (str(python_bin), "-m", "venv", str(venv_dir)), copy_root, connector_runtime=False),
                env,
                args.max_output_chars,
            )
            python_bin = _venv_python(venv_dir)
            _record_step(
                report,
                Step("install_editable_dev", (str(python_bin), "-m", "pip", "install", "-e", ".[dev]"), copy_root, connector_runtime=False),
                env,
                args.max_output_chars,
            )
            cli = _console_script(venv_dir, "aoa-4pda")
        else:
            env["PYTHONPATH"] = str(copy_root / "src")
            cli = python_bin

        for step in _route_steps(copy_root, python_bin, cli, args):
            _record_step(report, step, env, args.max_output_chars)

        state_leaks = _unexpected_connector_state_files(copy_root)
        report["repo_local_generated_state_leaks"] = state_leaks
        report["storage_artifacts"] = _storage_artifacts(storage_root)
        if state_leaks:
            report["status"] = "error"
            report["error"] = "generated connector state leaked into repo-local scaffold"
        else:
            report["status"] = "ok"
    except Exception as exc:  # noqa: BLE001 - verifier reports exact failure surface.
        report["status"] = "error"
        report["error"] = str(exc)
    finally:
        cleanup = report.get("status") == "ok" and not args.keep
        report["cleaned_up"] = bool(cleanup)
        if cleanup:
            shutil.rmtree(temp_root, ignore_errors=True)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("status") == "ok" else 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--keep", action="store_true", help="Keep the temporary copy and storage roots after success.")
    parser.add_argument("--skip-install", action="store_true", help="Use the current Python with PYTHONPATH instead of creating a venv.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip the full pytest step inside the copied repo.")
    parser.add_argument("--plan-only", action="store_true", help="Print the planned route without copying or running commands.")
    parser.add_argument("--max-output-chars", type=int, default=4000)
    return parser.parse_args(argv)


def _plan_payload(source_root: Path, args: argparse.Namespace) -> dict[str, object]:
    copy_root = Path("<temp>") / "repo"
    python_bin = Path("<temp>") / ".venv" / "bin" / "python"
    cli = Path("<temp>") / ".venv" / "bin" / "aoa-4pda"
    steps: list[Step] = []
    if not args.skip_install:
        steps.extend(
            [
                Step("create_venv", (str(Path(args.python)), "-m", "venv", str(Path("<temp>") / ".venv")), copy_root, connector_runtime=False),
                Step("install_editable_dev", (str(python_bin), "-m", "pip", "install", "-e", ".[dev]"), copy_root, connector_runtime=False),
            ]
        )
    steps.extend(_route_steps(copy_root, python_bin, cli, args))
    return {
        "schema": SCHEMA,
        "status": "plan",
        "source_root": str(source_root),
        "copy_excludes": sorted(IGNORED_NAMES),
        "connector_route_network_touched": False,
        "package_install_may_use_network": not args.skip_install,
        "steps": [_step_plan(step) for step in steps],
    }


def _route_steps(copy_root: Path, python_bin: Path, cli: Path, args: argparse.Namespace) -> list[Step]:
    cli_cmd = (str(cli),) if cli.name == "aoa-4pda" else (str(python_bin), "-m", "aoa_4pda_connector.cli")
    steps = [
        Step("validate_connector", (str(python_bin), "scripts/validate_connector.py"), copy_root, expect_json=True),
    ]
    if not args.skip_pytest:
        steps.append(Step("pytest", (str(python_bin), "-m", "pytest", "-q"), copy_root))
    steps.extend(
        [
            Step("doctor", (*cli_cmd, "doctor"), copy_root, expect_json=True),
            Step("storage_status", (*cli_cmd, "storage", "status"), copy_root, expect_json=True),
            Step("policy_check", (*cli_cmd, "policy", "check"), copy_root, expect_json=True),
            Step("ready_no_run", (*cli_cmd, "ready"), copy_root, expect_json=True),
            Step("discovery_audit_no_run", (*cli_cmd, "discovery", "audit", "xiaomi-13t"), copy_root, expect_json=True),
            Step("discovery_review_no_run", (*cli_cmd, "discovery", "review", "xiaomi-13t"), copy_root, expect_json=True),
            Step("coverage_audit_no_run", (*cli_cmd, "coverage", "audit", "xiaomi-13t"), copy_root, expect_json=True),
            Step("refresh_audit_no_run", (*cli_cmd, "refresh", "audit", "xiaomi-13t"), copy_root, expect_json=True),
            Step("starter_proof", (*cli_cmd, "proof", "starter"), copy_root, expect_json=True),
            Step("init_storage", (*cli_cmd, "init", "--apply"), copy_root, expect_json=True),
            Step("materialize_fixture", (*cli_cmd, "materialize", "fixture"), copy_root, expect_json=True),
            Step("query_graph_fixture", (*cli_cmd, "query-graph", DEFAULT_QUERY, "--run", "starter-fixture"), copy_root, expect_json=True),
            Step("query_hybrid_fixture", (*cli_cmd, "query-hybrid", DEFAULT_QUERY, "--run", "starter-fixture"), copy_root, expect_json=True),
            Step("answer_fixture", (*cli_cmd, "answer", DEFAULT_QUERY, "--run", "starter-fixture"), copy_root, expect_json=True),
            Step("eval_search_quality", (*cli_cmd, "eval", "search-quality"), copy_root, expect_json=True),
            Step("eval_graph_relations", (*cli_cmd, "eval", "graph-relations"), copy_root, expect_json=True),
            Step("eval_graph_query_packets", (*cli_cmd, "eval", "graph-query-packets"), copy_root, expect_json=True),
            Step("eval_hybrid_query_packets", (*cli_cmd, "eval", "hybrid-query-packets"), copy_root, expect_json=True),
            Step("eval_answer_packets", (*cli_cmd, "eval", "answer-packets"), copy_root, expect_json=True),
        ]
    )
    return steps


def _record_step(report: dict[str, object], step: Step, env: dict[str, str], max_output_chars: int) -> None:
    result = subprocess.run(
        step.command,
        cwd=step.cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    entry: dict[str, object] = {
        **_step_plan(step),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-max_output_chars:],
        "stderr_tail": result.stderr[-max_output_chars:],
    }
    if step.expect_json and result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            entry["json_schema"] = parsed.get("schema")
            entry["json_status"] = parsed.get("status")
            if parsed.get("network_touched") is True and step.connector_runtime:
                report["connector_route_network_touched"] = True
        except json.JSONDecodeError as exc:
            entry["json_error"] = str(exc)
    report.setdefault("steps", []).append(entry)
    if result.returncode != 0:
        raise RuntimeError(f"step failed: {step.step_id}")


def _step_plan(step: Step) -> dict[str, object]:
    return {
        "step_id": step.step_id,
        "command": list(step.command),
        "cwd": str(step.cwd),
        "connector_runtime": step.connector_runtime,
    }


def _copy_source_tree(source_root: Path, copy_root: Path) -> None:
    shutil.copytree(source_root, copy_root, ignore=_ignore_names)
    _prune_connector_state(copy_root)


def _ignore_names(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in IGNORED_NAMES or name.endswith(IGNORED_SUFFIXES):
            ignored.add(name)
    return ignored


def _prune_connector_state(repo_root: Path) -> None:
    root = repo_root / ".connector-state"
    if not root.exists():
        return
    for path in sorted(root.rglob("*"), key=lambda candidate: len(candidate.parts), reverse=True):
        rel = path.relative_to(repo_root).as_posix()
        if path.is_file() and rel not in ALLOWED_CONNECTOR_STATE_FILES:
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def _work_root(path: Path | None) -> Path:
    if path is not None:
        path.mkdir(parents=True, exist_ok=True)
        return path
    host_tmp = Path("/srv/abyss-machine/tmp/ai")
    if host_tmp.is_dir():
        return host_tmp
    return Path(tempfile.gettempdir())


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _console_script(venv_dir: Path, name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def _repo_state(repo_root: Path) -> dict[str, object]:
    return {
        "git_dir_copied": (repo_root / ".git").exists(),
        "connector_state_scaffold_exists": (repo_root / ".connector-state" / "README.md").is_file(),
        "unexpected_connector_state_files": _unexpected_connector_state_files(repo_root),
    }


def _unexpected_connector_state_files(repo_root: Path) -> list[str]:
    root = repo_root / ".connector-state"
    if not root.exists():
        return []
    unexpected: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if rel not in ALLOWED_CONNECTOR_STATE_FILES:
            unexpected.append(rel)
    return sorted(unexpected)


def _storage_artifacts(storage_root: Path) -> dict[str, object]:
    files = [path for path in storage_root.rglob("*") if path.is_file()] if storage_root.exists() else []
    return {
        "exists": storage_root.exists(),
        "file_count": len(files),
        "sample_files": [path.relative_to(storage_root).as_posix() for path in sorted(files)[:20]],
    }


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
