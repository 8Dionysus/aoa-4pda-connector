"""No-network refresh and freshness audit helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.config import LOCAL_STATE_DIR, StorageRoots, find_repo_root
from aoa_4pda_connector.coverage import audit_profile_coverage


REFRESH_TARGET = "reference-profile-refresh-v1"


def audit_profile_refresh(
    profile_id: str,
    repo_root: Path | None = None,
    roots: StorageRoots | None = None,
    *,
    run: str = "latest",
    max_age_hours: int = 168,
) -> dict[str, object]:
    """Return a no-network freshness and refresh audit for a profile run."""

    root = repo_root or find_repo_root()
    storage_roots = roots or StorageRoots.from_env(root)
    now = datetime.now(UTC).replace(microsecond=0)
    receipts = _receipt_chain(storage_roots, run)
    coverage = audit_profile_coverage(profile_id, root, storage_roots, run=run)
    crawl_receipt = receipts.get("crawl", {})
    normalize_receipt = receipts.get("normalize", {})
    index_receipt = receipts.get("index", {})
    vector_receipt = receipts.get("vector", {})
    graph_receipt = receipts.get("graph", {})
    timestamps = {
        "crawl_finished_at": _timestamp_report(crawl_receipt.get("finished_at"), now),
        "normalize_finished_at": _timestamp_report(normalize_receipt.get("finished_at"), now),
        "index_built_at": _timestamp_report(index_receipt.get("built_at"), now),
        "vector_built_at": _timestamp_report(vector_receipt.get("built_at"), now),
        "graph_built_at": _timestamp_report(graph_receipt.get("built_at"), now),
    }
    receipt_chain_present = all(receipts.get(kind) for kind in ["crawl", "normalize", "index", "vector", "graph"])
    crawl_age_hours = timestamps["crawl_finished_at"].get("age_hours")
    crawl_age_known = isinstance(crawl_age_hours, (int, float))
    crawl_age_within_limit = crawl_age_known and float(crawl_age_hours) <= max_age_hours
    crawl_counts = crawl_receipt.get("counts", {}) if isinstance(crawl_receipt.get("counts"), dict) else {}
    crawl_errors_zero = int(crawl_counts.get("errors", 0) or 0) == 0 if crawl_receipt else False
    policy = crawl_receipt.get("policy", {}) if isinstance(crawl_receipt.get("policy"), dict) else {}
    policy_ok = (
        policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False
    )
    derived_no_network = all(
        receipts.get(kind, {}).get("network_touched") is False for kind in ["normalize", "index", "vector", "graph"]
    )
    derived_order_ok = _derived_order_ok(timestamps)
    coverage_ready = coverage.get("status") == "coverage_ready"
    checks = {
        "receipt_chain_present": receipt_chain_present,
        "crawl_finished_at_present": timestamps["crawl_finished_at"]["parsed"] is True,
        "crawl_age_within_limit": bool(crawl_age_within_limit),
        "crawl_errors_zero": crawl_errors_zero,
        "crawl_policy_preserved": policy_ok,
        "derived_stages_network_free": derived_no_network,
        "derived_timestamps_present": all(
            timestamps[key]["parsed"] is True
            for key in ["normalize_finished_at", "index_built_at", "vector_built_at", "graph_built_at"]
        ),
        "derived_not_older_than_crawl": derived_order_ok,
        "coverage_ready": coverage_ready,
    }
    if not crawl_receipt:
        status = "missing_run"
    elif all(checks.values()):
        status = "fresh"
    else:
        status = "needs_refresh"

    return {
        "schema": "aoa_4pda_refresh_audit_v1",
        "target_status": REFRESH_TARGET,
        "status": status,
        "strict_ready": status == "fresh" and coverage_ready,
        "profile_id": profile_id,
        "run": run,
        "max_age_hours": max_age_hours,
        "now": now.isoformat().replace("+00:00", "Z"),
        "repo_root": str(root),
        "storage_mode": storage_roots.mode,
        "local_state_dir": LOCAL_STATE_DIR,
        "storage_roots": storage_roots.as_dict(),
        "receipt_run_ids": _receipt_run_ids(receipts),
        "timestamps": timestamps,
        "coverage_status": coverage.get("status"),
        "coverage_summary": _coverage_summary(coverage),
        "checks": checks,
        "gaps": _refresh_gaps(checks, coverage),
        "refresh_plan": _refresh_plan(profile_id, run, coverage),
        "next_actions": _next_actions(status, checks, coverage),
        "network_touched": False,
    }


def _receipt_chain(roots: StorageRoots, run: str) -> dict[str, dict[str, object]]:
    receipts: dict[str, dict[str, object]] = {}
    if roots.artifact is None:
        return receipts
    receipt_dir = roots.artifact / "receipts"
    for kind in ["crawl", "normalize", "index", "vector", "graph"]:
        path = receipt_dir / f"latest_{kind}.json" if run == "latest" else receipt_dir / f"{run}.{kind}.json"
        receipts[kind] = _load_json(path)
    return receipts


def _receipt_run_ids(receipts: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        kind: receipt.get("run_id") or receipt.get("index_id") or receipt.get("vector_id")
        for kind, receipt in sorted(receipts.items())
    }


def _timestamp_report(value: object, now: datetime) -> dict[str, object]:
    parsed = _parse_timestamp(value)
    if parsed is None:
        return {"value": value, "parsed": False, "age_hours": None}
    age_hours = max(0.0, (now - parsed).total_seconds() / 3600)
    return {
        "value": parsed.isoformat().replace("+00:00", "Z"),
        "parsed": True,
        "age_hours": round(age_hours, 2),
    }


def _parse_timestamp(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).replace(microsecond=0)


def _derived_order_ok(timestamps: dict[str, dict[str, object]]) -> bool:
    crawl = _parse_timestamp(timestamps["crawl_finished_at"].get("value"))
    normalize = _parse_timestamp(timestamps["normalize_finished_at"].get("value"))
    index = _parse_timestamp(timestamps["index_built_at"].get("value"))
    vector = _parse_timestamp(timestamps["vector_built_at"].get("value"))
    graph = _parse_timestamp(timestamps["graph_built_at"].get("value"))
    if not all([crawl, normalize, index, vector, graph]):
        return False
    return bool(normalize >= crawl and index >= normalize and vector >= normalize and graph >= normalize)


def _coverage_summary(coverage: dict[str, object]) -> dict[str, object]:
    coverage_section = coverage.get("coverage", {}) if isinstance(coverage.get("coverage"), dict) else {}
    seed_pages = coverage_section.get("seed_pages", {}) if isinstance(coverage_section.get("seed_pages"), dict) else {}
    focus_areas = (
        coverage_section.get("focus_areas", {}) if isinstance(coverage_section.get("focus_areas"), dict) else {}
    )
    materialized = coverage.get("materialized", {}) if isinstance(coverage.get("materialized"), dict) else {}
    index = materialized.get("index", {}) if isinstance(materialized.get("index"), dict) else {}
    vector = materialized.get("vector", {}) if isinstance(materialized.get("vector"), dict) else {}
    graph = materialized.get("graph", {}) if isinstance(materialized.get("graph"), dict) else {}
    return {
        "seed_pages": seed_pages,
        "focus_areas": focus_areas,
        "index_doc_count": index.get("doc_count"),
        "vector_doc_count": vector.get("doc_count"),
        "graph_edge_count": graph.get("edge_count"),
    }


def _refresh_gaps(checks: dict[str, bool], coverage: dict[str, object]) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    for check, ok in checks.items():
        if not ok:
            gaps.append({"check": check})
    coverage_gaps = coverage.get("gaps", [])
    if isinstance(coverage_gaps, list):
        gaps.extend({"check": "coverage_gap", "details": gap} for gap in coverage_gaps)
    return gaps


def _refresh_plan(profile_id: str, run: str, coverage: dict[str, object]) -> dict[str, object]:
    seed_plan = coverage.get("seed_plan", {}) if isinstance(coverage.get("seed_plan"), dict) else {}
    return {
        "network_touched": False,
        "operator_confirmation_required_for_crawl": True,
        "profile_id": profile_id,
        "selected_run": run,
        "seed_count": seed_plan.get("seed_count"),
        "expected_page_count": seed_plan.get("expected_page_count"),
        "commands": [
            f"aoa-4pda crawl --profile {profile_id}",
            "aoa-4pda normalize --run latest",
            f"aoa-4pda build-index --profile {profile_id} --run latest",
            f"aoa-4pda build-vector --profile {profile_id} --run latest",
            f"aoa-4pda build-graph --profile {profile_id} --run latest",
            f"aoa-4pda coverage audit {profile_id} --run latest",
            f"aoa-4pda refresh audit {profile_id} --run latest",
        ],
    }


def _next_actions(status: str, checks: dict[str, bool], coverage: dict[str, object]) -> list[str]:
    if status == "fresh":
        return ["Run search, hybrid, graph-query, answer, and live eval gates against the same named run."]
    actions: list[str] = []
    if not checks.get("receipt_chain_present"):
        actions.append("Create or restore a crawl -> normalize -> build-index -> build-vector -> build-graph receipt chain.")
    if not checks.get("crawl_age_within_limit"):
        actions.append("Refresh the bounded profile after operator confirmation, then rebuild derived artifacts.")
    if not checks.get("derived_not_older_than_crawl"):
        actions.append("Re-run normalize, build-index, build-vector, and build-graph for the selected crawl run.")
    if coverage.get("status") != "coverage_ready":
        actions.append("Resolve coverage gaps before treating the reference profile as ready for deep answers.")
    if not actions:
        actions.append("Inspect refresh gaps and rerun the audit after the next bounded update.")
    return actions


def _load_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
