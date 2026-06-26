"""No-network profile coverage audit helpers."""

from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.config import LOCAL_STATE_DIR, StorageRoots, find_repo_root
from aoa_4pda_connector.fetch import topic_id_from_url, topic_page_start_from_url, topic_page_url
from aoa_4pda_connector.policy import is_url_allowed
from aoa_4pda_connector.storage import storage_status


COVERAGE_TARGET = "reference-profile-coverage-v1"


def audit_profile_coverage(
    profile_id: str,
    repo_root: Path | None = None,
    roots: StorageRoots | None = None,
    *,
    run: str = "latest",
) -> dict[str, object]:
    """Return a no-network coverage audit for a bounded profile run."""

    root = repo_root or find_repo_root()
    storage_roots = roots or StorageRoots.from_env(root)
    profile_path = root / "connector" / "profiles" / f"{profile_id}.yaml"
    if not profile_path.is_file():
        return {
            "schema": "aoa_4pda_coverage_audit_v1",
            "target_status": COVERAGE_TARGET,
            "status": "error",
            "profile_id": profile_id,
            "run": run,
            "error": f"profile not found: {profile_path.relative_to(root)}",
            "network_touched": False,
        }

    profile = _read_profile(profile_path)
    seed_rel = str(profile.get("seed_file", "connector/seeds/starter_topics.yaml"))
    seed_path = root / seed_rel
    seeds = _read_seed_urls(seed_path) if seed_path.is_file() else []
    default_pages = _int_value(profile.get("max_pages_per_topic"), 1)
    seed_plan = [_seed_plan(seed, default_pages) for seed in seeds]
    expected_page_keys = {
        (str(seed["seed_id"]), int(page_start))
        for seed in seed_plan
        for page_start in seed["expected_page_starts"]
    }

    receipts = _receipt_chain(storage_roots, run)
    crawl_receipt = receipts.get("crawl", {})
    normalize_receipt = receipts.get("normalize", {})
    index_receipt = receipts.get("index", {})
    vector_receipt = receipts.get("vector", {})
    graph_receipt = receipts.get("graph", {})
    fetched_pages = _fetched_pages(crawl_receipt)
    fetched_page_keys = {(item["seed_id"], item["page_start"]) for item in fetched_pages}
    fetched_seed_ids = sorted({seed_id for seed_id, _page_start in fetched_page_keys})
    seed_by_id = {str(seed["seed_id"]): seed for seed in seed_plan}
    captured_focus = sorted(
        {
            str(seed_by_id[seed_id]["focus"])
            for seed_id in fetched_seed_ids
            if seed_id in seed_by_id and seed_by_id[seed_id].get("focus")
        }
    )
    expected_focus = sorted({str(seed["focus"]) for seed in seed_plan if seed.get("focus")})
    missing_page_keys = sorted(expected_page_keys - fetched_page_keys)
    missing_seed_ids = sorted(set(seed_by_id) - set(fetched_seed_ids))
    missing_focus = sorted(set(expected_focus) - set(captured_focus))

    normalized = _normalized_materialization(normalize_receipt)
    index = _index_materialization(index_receipt)
    vector = _vector_materialization(vector_receipt)
    graph = _graph_materialization(graph_receipt)
    quality_gates = _quality_gates(root, profile)
    information_needs = _information_need_coverage(root, profile, seed_plan, captured_focus, quality_gates)
    policy = crawl_receipt.get("policy", {}) if isinstance(crawl_receipt.get("policy"), dict) else {}
    receipt_chain_present = all(receipts.get(kind) for kind in ["crawl", "normalize", "index", "vector", "graph"])
    receipt_run_ids = _receipt_run_ids(receipts)
    receipts_share_run = _receipts_share_run(receipts)
    receipt_profile_matches = (
        crawl_receipt.get("profile_id") == profile_id
        and index_receipt.get("profile_id") == profile_id
        and vector_receipt.get("profile_id") == profile_id
        and graph_receipt.get("profile_id") == profile_id
    )
    policy_ok = (
        policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False
    )
    derived_no_network = all(
        receipts.get(kind, {}).get("network_touched") is False for kind in ["normalize", "index", "vector", "graph"]
    )
    seed_urls_allowed = all(is_url_allowed(str(seed.get("url", ""))) for seed in seed_plan)
    all_quality_gates_present = all(gate["exists"] for gate in quality_gates.values())
    checks = {
        "profile_exists": profile_path.is_file(),
        "seed_file_exists": seed_path.is_file(),
        "seed_urls_allowed_public_topics": seed_urls_allowed,
        "receipt_chain_present": receipt_chain_present,
        "receipts_share_run": receipts_share_run,
        "receipt_profile_matches": receipt_profile_matches,
        "crawl_policy_preserved": policy_ok,
        "derived_stages_network_free": derived_no_network,
        "all_expected_seed_pages_fetched": bool(expected_page_keys) and not missing_page_keys,
        "normalized_pages_cover_fetched_pages": normalized["page_count"] >= len(fetched_page_keys)
        if fetched_page_keys
        else False,
        "index_has_docs": index["doc_count"] > 0,
        "vector_has_docs": vector["doc_count"] > 0,
        "graph_has_edges": graph["edge_count"] > 0,
        "quality_gate_suites_present": all_quality_gates_present,
        "information_need_matrix_present": bool(information_needs.get("matrix_exists")),
        "deep_information_needs_covered": bool(
            information_needs.get("summary", {}).get("deep_profile_complete")
            if isinstance(information_needs.get("summary"), dict)
            else False
        ),
    }
    gaps = _coverage_gaps(checks, missing_seed_ids, missing_page_keys, missing_focus, information_needs)
    if not crawl_receipt:
        status = "no_run"
    elif all(checks.values()):
        status = "coverage_ready"
    else:
        status = "partial"

    return {
        "schema": "aoa_4pda_coverage_audit_v1",
        "target_status": COVERAGE_TARGET,
        "status": status,
        "profile_id": profile_id,
        "run": run,
        "repo_root": str(root),
        "storage_mode": storage_roots.mode,
        "local_state_dir": LOCAL_STATE_DIR,
        "storage_roots": storage_roots.as_dict(),
        "profile": {
            "path": str(profile_path.relative_to(root)),
            "profile_kind": profile.get("profile_kind"),
            "target_label": profile.get("target_label"),
            "target_codename": profile.get("target_codename"),
            "seed_file": seed_rel,
            "max_topics": profile.get("max_topics"),
            "max_pages_per_topic": profile.get("max_pages_per_topic"),
        },
        "seed_plan": {
            "seed_file_exists": seed_path.is_file(),
            "seed_count": len(seed_plan),
            "expected_page_count": len(expected_page_keys),
            "expected_focus_areas": expected_focus,
            "topics": sorted({str(seed["topic_id"]) for seed in seed_plan}),
            "seeds": seed_plan,
        },
        "materialized": {
            "receipt_chain_present": receipt_chain_present,
            "receipt_run_ids": receipt_run_ids,
            "crawl_profile_id": crawl_receipt.get("profile_id"),
            "crawl_counts": crawl_receipt.get("counts", {}),
            "fetched_seed_ids": fetched_seed_ids,
            "fetched_page_count": len(fetched_page_keys),
            "fetched_pages": fetched_pages,
            "normalized": normalized,
            "index": index,
            "vector": vector,
            "graph": graph,
        },
        "coverage": {
            "seed_pages": {
                "expected": len(expected_page_keys),
                "fetched": len(fetched_page_keys),
                "missing": len(missing_page_keys),
                "ratio": _ratio(len(fetched_page_keys), len(expected_page_keys)),
            },
            "seeds": {
                "expected": len(seed_plan),
                "fetched": len(fetched_seed_ids),
                "missing": len(missing_seed_ids),
                "missing_seed_ids": missing_seed_ids,
            },
            "focus_areas": {
                "expected": len(expected_focus),
                "captured": len(captured_focus),
                "missing": len(missing_focus),
                "captured_focus_areas": captured_focus,
                "missing_focus_areas": missing_focus,
            },
            "missing_pages": [
                {"seed_id": seed_id, "page_start": page_start} for seed_id, page_start in missing_page_keys
            ],
        },
        "quality_gates": quality_gates,
        "information_needs": information_needs,
        "checks": checks,
        "gaps": gaps,
        "next_actions": _next_actions(status, gaps),
        "storage_status": storage_status(root, storage_roots),
        "network_touched": False,
    }


def _read_profile(path: Path) -> dict[str, object]:
    values: dict[str, object] = {"seed_file": "connector/seeds/starter_topics.yaml"}
    string_keys = {
        "schema",
        "profile_id",
        "profile_kind",
        "description",
        "target_device_id",
        "target_label",
        "target_codename",
        "target_model_aliases",
        "target_search_terms",
        "network_default",
        "seed_file",
        "allowlist_manifest",
        "information_need_matrix",
        "live_search_suite",
        "live_ranking_pressure_suite",
        "live_hybrid_query_suite",
        "live_graph_query_suite",
        "live_answer_suite",
        "claim_graph_suite",
        "claim_answer_suite",
    }
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {"max_topics", "max_pages_per_topic", "max_posts_per_topic", "min_delay_seconds", "max_concurrency"}:
            values[key] = _int_value(value, 0)
        elif key in string_keys and value:
            values[key] = value
    return values


def _read_seed_urls(path: Path) -> list[dict[str, str]]:
    seeds: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- id:"):
            if current:
                seeds.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif current and line.startswith("url:"):
            current["url"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("label:"):
            current["label"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("status:"):
            current["status"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("focus:"):
            current["focus"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("max_pages:"):
            current["max_pages"] = line.split(":", 1)[1].strip()
    if current:
        seeds.append(current)
    return [seed for seed in seeds if seed.get("url")]


def _seed_plan(seed: dict[str, str], default_pages: int) -> dict[str, object]:
    expected_pages = _int_value(seed.get("max_pages"), default_pages)
    page_urls = [topic_page_url(seed["url"], page_index) for page_index in range(max(1, expected_pages))]
    return {
        "seed_id": seed.get("id"),
        "url": seed.get("url"),
        "label": seed.get("label"),
        "focus": seed.get("focus"),
        "topic_id": topic_id_from_url(str(seed.get("url", ""))),
        "expected_pages": len(page_urls),
        "expected_page_starts": [int(topic_page_start_from_url(url)) for url in page_urls],
        "allowed_public_topic": is_url_allowed(str(seed.get("url", ""))),
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


def _fetched_pages(crawl_receipt: dict[str, object]) -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    snapshots = crawl_receipt.get("snapshots", [])
    if not isinstance(snapshots, list):
        return pages
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        seed_id = snapshot.get("seed_id")
        page_start = snapshot.get("page_start")
        url = str(snapshot.get("url", ""))
        if page_start is None and url:
            page_start = topic_page_start_from_url(url)
        if not seed_id or page_start is None:
            continue
        pages.append(
            {
                "seed_id": str(seed_id),
                "page_start": _int_value(page_start, 0),
                "url": url,
                "path_exists": Path(str(snapshot.get("path", ""))).is_file(),
                "status": snapshot.get("status"),
                "bytes": snapshot.get("bytes"),
            }
        )
    return sorted(pages, key=lambda item: (str(item["seed_id"]), int(item["page_start"])))


def _normalized_materialization(receipt: dict[str, object]) -> dict[str, object]:
    paths = [
        Path(str(item.get("path", "")))
        for item in receipt.get("normalized", [])
        if isinstance(item, dict) and item.get("path")
    ]
    page_count = 0
    post_count = 0
    topic_ids: set[str] = set()
    missing_paths: list[str] = []
    for path in paths:
        if not path.is_file():
            missing_paths.append(str(path))
            continue
        page_count += 1
        topic = _load_json(path)
        if topic.get("topic_id"):
            topic_ids.add(str(topic["topic_id"]))
        posts = topic.get("posts", [])
        if isinstance(posts, list):
            post_count += len(posts)
    counts = receipt.get("counts", {}) if isinstance(receipt.get("counts"), dict) else {}
    return {
        "receipt_counts": counts,
        "page_count": page_count or _int_value(counts.get("pages"), 0),
        "topic_count": len(topic_ids) or _int_value(counts.get("topics"), 0),
        "post_count": post_count,
        "missing_paths": missing_paths,
    }


def _index_materialization(receipt: dict[str, object]) -> dict[str, object]:
    path = Path(str(receipt.get("index_path", "")))
    payload = _load_json(path) if path.is_file() else {}
    return {
        "path": str(path) if receipt.get("index_path") else None,
        "path_exists": path.is_file(),
        "profile_id": receipt.get("profile_id"),
        "doc_count": _int_value(payload.get("doc_count"), 0),
        "term_count": _int_value(payload.get("term_count"), 0),
        "index_kinds": receipt.get("index_kinds", []),
    }


def _vector_materialization(receipt: dict[str, object]) -> dict[str, object]:
    path = Path(str(receipt.get("vector_path", "")))
    payload = _load_json(path) if path.is_file() else {}
    return {
        "path": str(path) if receipt.get("vector_path") else None,
        "path_exists": path.is_file(),
        "profile_id": receipt.get("profile_id"),
        "doc_count": _int_value(payload.get("doc_count"), 0),
        "feature_count": _int_value(payload.get("feature_count"), 0),
        "dimensions": _int_value(payload.get("dimensions"), 0),
        "algorithm": payload.get("algorithm") or receipt.get("vector_algorithm"),
        "index_kinds": receipt.get("index_kinds", []),
    }


def _graph_materialization(receipt: dict[str, object]) -> dict[str, object]:
    path = Path(str(receipt.get("graph_path", "")))
    payload = _load_json(path) if path.is_file() else {}
    claim_stats = payload.get("claim_stats", {}) if isinstance(payload.get("claim_stats"), dict) else {}
    return {
        "path": str(path) if receipt.get("graph_path") else None,
        "path_exists": path.is_file(),
        "profile_id": receipt.get("profile_id"),
        "node_count": _int_value(payload.get("node_count"), 0),
        "edge_count": _int_value(payload.get("edge_count"), 0),
        "claim_stats": claim_stats,
        "claim_count": _int_value(claim_stats.get("claim_count"), 0),
        "supersedes_count": _int_value(claim_stats.get("supersedes_count"), 0),
        "contradicts_count": _int_value(claim_stats.get("contradicts_count"), 0),
        "contextualizes_count": _int_value(claim_stats.get("contextualizes_count"), 0),
    }


def _quality_gates(repo_root: Path, profile: dict[str, object]) -> dict[str, dict[str, object]]:
    gates: dict[str, dict[str, object]] = {}
    for key in [
        "live_search_suite",
        "live_ranking_pressure_suite",
        "live_hybrid_query_suite",
        "live_graph_query_suite",
        "live_answer_suite",
        "claim_graph_suite",
        "claim_answer_suite",
    ]:
        rel = str(profile.get(key, ""))
        path = repo_root / rel if rel else None
        suite = _load_json(path) if path and path.is_file() else {}
        cases = suite.get("cases", []) if isinstance(suite.get("cases"), list) else []
        gates[key] = {
            "path": rel or None,
            "exists": bool(path and path.is_file()),
            "suite_id": suite.get("suite_id"),
            "case_count": len(cases),
            "case_ids": [
                str(case.get("case_id"))
                for case in cases
                if isinstance(case, dict) and case.get("case_id")
            ],
        }
    return gates


def _information_need_coverage(
    repo_root: Path,
    profile: dict[str, object],
    seed_plan: list[dict[str, object]],
    captured_focus: list[str],
    quality_gates: dict[str, dict[str, object]],
) -> dict[str, object]:
    rel = str(profile.get("information_need_matrix", "") or "")
    path = repo_root / rel if rel else None
    matrix = _load_json(path) if path and path.is_file() else {}
    raw_needs = matrix.get("needs", []) if isinstance(matrix.get("needs"), list) else []
    expected_focus = sorted({str(seed["focus"]) for seed in seed_plan if seed.get("focus")})
    captured_focus_set = set(captured_focus)
    expected_focus_set = set(expected_focus)
    suite_case_ids = {
        key: set(str(case_id) for case_id in gate.get("case_ids", []))
        for key, gate in quality_gates.items()
        if isinstance(gate, dict)
    }

    needs: list[dict[str, object]] = []
    for raw_need in raw_needs:
        if not isinstance(raw_need, dict):
            continue
        focus_any = _string_list(raw_need.get("seed_focus_any"))
        planned_focus = sorted(expected_focus_set.intersection(focus_any))
        captured_need_focus = sorted(captured_focus_set.intersection(focus_any))
        eval_cases = raw_need.get("eval_cases", {})
        eval_routes = _need_eval_routes(eval_cases, suite_case_ids)
        eval_case_count = sum(len(route["case_ids"]) for route in eval_routes.values())
        eval_route_present = eval_case_count > 0 and all(
            not route["missing_case_ids"] for route in eval_routes.values()
        )
        eval_required = bool(raw_need.get("eval_required", True))
        if not planned_focus:
            status = "missing_seed_focus"
        elif not captured_need_focus:
            status = "unmaterialized"
        elif eval_required and not eval_route_present:
            status = "missing_eval_route"
        else:
            status = "covered"
        needs.append(
            {
                "need_id": raw_need.get("need_id"),
                "label": raw_need.get("label"),
                "priority": raw_need.get("priority", "required"),
                "required_for_connector_ready": bool(raw_need.get("required_for_connector_ready", False)),
                "required_for_deep_profile": bool(raw_need.get("required_for_deep_profile", True)),
                "status": status,
                "seed_focus_any": focus_any,
                "planned_focus_areas": planned_focus,
                "captured_focus_areas": captured_need_focus,
                "eval_route_present": eval_route_present,
                "eval_case_count": eval_case_count,
                "eval_routes": eval_routes,
            }
        )

    summary = _information_need_summary(needs)
    return {
        "schema": matrix.get("schema") or "aoa_4pda_information_need_coverage_v1",
        "matrix_path": rel or None,
        "matrix_exists": bool(path and path.is_file()),
        "matrix_profile_id": matrix.get("profile_id"),
        "expected_focus_areas": expected_focus,
        "captured_focus_areas": captured_focus,
        "summary": summary,
        "needs": needs,
    }


def _need_eval_routes(
    eval_cases: object,
    suite_case_ids: dict[str, set[str]],
) -> dict[str, dict[str, object]]:
    if not isinstance(eval_cases, dict):
        return {}
    routes: dict[str, dict[str, object]] = {}
    for gate_key, raw_case_ids in sorted(eval_cases.items()):
        case_ids = _string_list(raw_case_ids)
        present = sorted(set(case_ids).intersection(suite_case_ids.get(str(gate_key), set())))
        missing = sorted(set(case_ids) - suite_case_ids.get(str(gate_key), set()))
        routes[str(gate_key)] = {
            "case_ids": case_ids,
            "present_case_ids": present,
            "missing_case_ids": missing,
        }
    return routes


def _information_need_summary(needs: list[dict[str, object]]) -> dict[str, object]:
    statuses: dict[str, int] = {}
    connector_ready_required = [need for need in needs if need.get("required_for_connector_ready")]
    deep_required = [need for need in needs if need.get("required_for_deep_profile")]
    for need in needs:
        status = str(need.get("status", "unknown"))
        statuses[status] = statuses.get(status, 0) + 1
    connector_ready_missing = [
        str(need.get("need_id"))
        for need in connector_ready_required
        if need.get("status") != "covered"
    ]
    deep_missing = [
        str(need.get("need_id"))
        for need in deep_required
        if need.get("status") != "covered"
    ]
    return {
        "total": len(needs),
        "status_counts": statuses,
        "covered": statuses.get("covered", 0),
        "connector_ready_required": len(connector_ready_required),
        "connector_ready_covered": len(connector_ready_required) - len(connector_ready_missing),
        "connector_ready_missing_need_ids": connector_ready_missing,
        "connector_ready_complete": bool(connector_ready_required) and not connector_ready_missing,
        "deep_profile_required": len(deep_required),
        "deep_profile_covered": len(deep_required) - len(deep_missing),
        "deep_profile_missing_need_ids": deep_missing,
        "deep_profile_complete": bool(deep_required) and not deep_missing,
    }


def _coverage_gaps(
    checks: dict[str, bool],
    missing_seed_ids: list[str],
    missing_page_keys: list[tuple[str, int]],
    missing_focus: list[str],
    information_needs: dict[str, object],
) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    for check, ok in checks.items():
        if ok:
            continue
        gap: dict[str, object] = {"check": check}
        if check == "all_expected_seed_pages_fetched":
            gap["missing_seed_ids"] = missing_seed_ids
            gap["missing_pages"] = [
                {"seed_id": seed_id, "page_start": page_start} for seed_id, page_start in missing_page_keys
            ]
            gap["missing_focus_areas"] = missing_focus
        if check == "deep_information_needs_covered":
            summary = information_needs.get("summary", {}) if isinstance(information_needs, dict) else {}
            if isinstance(summary, dict):
                gap["deep_profile_missing_need_ids"] = summary.get("deep_profile_missing_need_ids", [])
                gap["connector_ready_missing_need_ids"] = summary.get("connector_ready_missing_need_ids", [])
        gaps.append(gap)
    return gaps


def _next_actions(status: str, gaps: list[dict[str, object]]) -> list[str]:
    if status == "coverage_ready":
        return ["Run focused search, hybrid, graph, answer, and live quality gates against the same named run."]
    actions: list[str] = []
    gap_ids = {str(gap.get("check")) for gap in gaps}
    if "receipt_chain_present" in gap_ids:
        actions.append("Create or restore a crawl -> normalize -> build-index -> build-vector -> build-graph receipt chain.")
    if "all_expected_seed_pages_fetched" in gap_ids:
        actions.append("Expand the bounded profile run until the seed coverage report has no missing pages.")
    if "index_has_docs" in gap_ids:
        actions.append("Build the keyword index for the same run before judging retrieval coverage.")
    if "vector_has_docs" in gap_ids:
        actions.append("Build the deterministic vector index for the same run before judging hybrid retrieval coverage.")
    if "graph_has_edges" in gap_ids:
        actions.append("Build the graph export for the same run before judging graph/answer coverage.")
    if "quality_gate_suites_present" in gap_ids:
        actions.append("Restore the profile quality-gate suites before claiming reference-profile coverage.")
    if "information_need_matrix_present" in gap_ids:
        actions.append("Restore the profile information-need matrix before judging deep reference-profile usefulness.")
    if "deep_information_needs_covered" in gap_ids:
        actions.append("Add or restore eval routes for uncovered Xiaomi 13T information needs before claiming deep profile coverage.")
    if not actions:
        actions.append("Inspect gaps and rerun coverage audit after the next bounded materialization step.")
    return actions


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _receipt_run_ids(receipts: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        kind: receipt.get("run_id") or receipt.get("index_id") or receipt.get("vector_id")
        for kind, receipt in sorted(receipts.items())
    }


def _receipts_share_run(receipts: dict[str, dict[str, object]]) -> bool:
    if set(receipts) != {"crawl", "normalize", "index", "vector", "graph"}:
        return False
    run_ids = [value for value in _receipt_run_ids(receipts).values() if value]
    return len(run_ids) == 5 and len(set(run_ids)) == 1


def _load_json(path: Path | None) -> dict[str, object]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _int_value(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)
