"""Local eval runners for connector-owned retrieval checks."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from aoa_4pda_connector.answer import render_answer_packet
from aoa_4pda_connector.config import StorageRoots, find_repo_root
from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.query import query_graph_packet, query_hybrid_packet, query_keyword_index
from aoa_4pda_connector.vector import build_vector_index


DEFAULT_SEARCH_EVAL_SUITE = Path("evals/suites/starter_search_quality.json")
DEFAULT_GRAPH_EVAL_SUITE = Path("evals/suites/starter_graph_relations.json")
DEFAULT_GRAPH_QUERY_EVAL_SUITE = Path("evals/suites/starter_graph_query_packets.json")
DEFAULT_HYBRID_QUERY_EVAL_SUITE = Path("evals/suites/starter_hybrid_query_packets.json")
DEFAULT_ANSWER_EVAL_SUITE = Path("evals/suites/starter_answer_packets.json")
DEFAULT_LIVE_SEARCH_EVAL_SUITE = Path("evals/suites/live_starter_search_quality.json")
DEFAULT_LIVE_HYBRID_QUERY_EVAL_SUITE = Path("evals/suites/live_xiaomi_13t_hybrid_query_quality.json")
DEFAULT_LIVE_GRAPH_QUERY_EVAL_SUITE = Path("evals/suites/live_xiaomi_13t_graph_query_quality.json")
DEFAULT_LIVE_ANSWER_EVAL_SUITE = Path("evals/suites/live_xiaomi_13t_answer_quality.json")


def run_search_eval_suite(suite_path: Path | None = None, repo_root: Path | None = None) -> dict[str, object]:
    """Run a small public-safe search eval suite without touching the network."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_SEARCH_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    dataset = suite.get("dataset", {})
    fixture_path = _resolve_repo_path(root, Path(str(dataset.get("topic_fixture", ""))))

    with tempfile.TemporaryDirectory(prefix="aoa-4pda-search-eval-") as tmp:
        eval_root = Path(tmp)
        normalized_dir = eval_root / "normalized"
        normalized_dir.mkdir(parents=True)
        fixture_topic = json.loads(fixture_path.read_text(encoding="utf-8"))
        topic_id = str(fixture_topic.get("topic_id", "fixture"))
        shutil.copy2(fixture_path, normalized_dir / f"topic-{topic_id}.json")
        index_path = build_keyword_index(normalized_dir, eval_root / "index", "eval")
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))

        case_reports = [
            _run_case(case, index_path)
            for case in suite.get("cases", [])
        ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    return {
        "schema": "aoa_4pda_search_eval_report_v1",
        "status": "ok" if not failed else "error",
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
        },
        "network_touched": False,
        "artifact_lifecycle": "temporary_deleted_after_run",
        "cases": case_reports,
    }


def run_graph_eval_suite(suite_path: Path | None = None, repo_root: Path | None = None) -> dict[str, object]:
    """Run a small public-safe graph relation eval suite without touching the network."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_GRAPH_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    dataset = suite.get("dataset", {})
    fixture_path = _resolve_repo_path(root, Path(str(dataset.get("html_fixture", ""))))
    source_url = str(dataset.get("source_url", ""))

    with tempfile.TemporaryDirectory(prefix="aoa-4pda-graph-eval-") as tmp:
        eval_root = Path(tmp)
        normalized_dir = eval_root / "normalized"
        normalize_snapshot(fixture_path, source_url, normalized_dir)
        graph_path = build_graph(normalized_dir, eval_root / "graph", "eval")
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        case_reports = [_run_graph_case(case, graph) for case in suite.get("cases", [])]

    failed = [case for case in case_reports if case["status"] != "ok"]
    return {
        "schema": "aoa_4pda_graph_eval_report_v1",
        "status": "ok" if not failed else "error",
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
        },
        "graph": {
            "node_count": graph.get("node_count"),
            "edge_count": graph.get("edge_count"),
        },
        "network_touched": False,
        "artifact_lifecycle": "temporary_deleted_after_run",
        "cases": case_reports,
    }


def run_graph_query_eval_suite(suite_path: Path | None = None, repo_root: Path | None = None) -> dict[str, object]:
    """Run a small public-safe graph query packet eval suite without touching the network."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_GRAPH_QUERY_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    dataset = suite.get("dataset", {})
    fixture_path = _resolve_repo_path(root, Path(str(dataset.get("html_fixture", ""))))
    source_url = str(dataset.get("source_url", ""))

    with tempfile.TemporaryDirectory(prefix="aoa-4pda-graph-query-eval-") as tmp:
        eval_root = Path(tmp)
        normalized_dir = eval_root / "normalized"
        normalize_snapshot(fixture_path, source_url, normalized_dir)
        index_path = build_keyword_index(normalized_dir, eval_root / "index", "eval")
        graph_path = build_graph(normalized_dir, eval_root / "graph", "eval")
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
        case_reports = [
            _run_graph_query_case(case, index_path, graph_path)
            for case in suite.get("cases", [])
        ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    return {
        "schema": "aoa_4pda_graph_query_eval_report_v1",
        "status": "ok" if not failed else "error",
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
        },
        "graph": {
            "node_count": graph_payload.get("node_count"),
            "edge_count": graph_payload.get("edge_count"),
        },
        "network_touched": False,
        "artifact_lifecycle": "temporary_deleted_after_run",
        "cases": case_reports,
    }


def run_answer_eval_suite(suite_path: Path | None = None, repo_root: Path | None = None) -> dict[str, object]:
    """Run a small public-safe rendered-answer eval suite without touching the network."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_ANSWER_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    dataset = suite.get("dataset", {})
    fixture_path = _resolve_repo_path(root, Path(str(dataset.get("html_fixture", ""))))
    source_url = str(dataset.get("source_url", ""))

    with tempfile.TemporaryDirectory(prefix="aoa-4pda-answer-eval-") as tmp:
        eval_root = Path(tmp)
        normalized_dir = eval_root / "normalized"
        normalize_snapshot(fixture_path, source_url, normalized_dir)
        index_path = build_keyword_index(normalized_dir, eval_root / "index", "eval")
        graph_path = build_graph(normalized_dir, eval_root / "graph", "eval")
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
        case_reports = [
            _run_answer_case(case, index_path, graph_path)
            for case in suite.get("cases", [])
        ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    return {
        "schema": "aoa_4pda_answer_eval_report_v1",
        "status": "ok" if not failed else "error",
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
        },
        "graph": {
            "node_count": graph_payload.get("node_count"),
            "edge_count": graph_payload.get("edge_count"),
        },
        "network_touched": False,
        "artifact_lifecycle": "temporary_deleted_after_run",
        "cases": case_reports,
    }


def run_hybrid_query_eval_suite(suite_path: Path | None = None, repo_root: Path | None = None) -> dict[str, object]:
    """Run a small public-safe hybrid query packet eval without touching the network."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_HYBRID_QUERY_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    dataset = suite.get("dataset", {})
    fixture_path = _resolve_repo_path(root, Path(str(dataset.get("html_fixture", ""))))
    source_url = str(dataset.get("source_url", ""))

    with tempfile.TemporaryDirectory(prefix="aoa-4pda-hybrid-query-eval-") as tmp:
        eval_root = Path(tmp)
        normalized_dir = eval_root / "normalized"
        normalize_snapshot(fixture_path, source_url, normalized_dir)
        index_path = build_keyword_index(normalized_dir, eval_root / "index", "eval")
        vector_path = build_vector_index(normalized_dir, eval_root / "vector", "eval")
        graph_path = build_graph(normalized_dir, eval_root / "graph", "eval")
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        vector_payload = json.loads(vector_path.read_text(encoding="utf-8"))
        graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
        case_reports = [
            _run_hybrid_query_case(case, index_path, vector_path, graph_path)
            for case in suite.get("cases", [])
        ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    return {
        "schema": "aoa_4pda_hybrid_query_eval_report_v1",
        "status": "ok" if not failed else "error",
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
        },
        "vector": {
            "unit": vector_payload.get("unit"),
            "doc_count": vector_payload.get("doc_count"),
            "feature_count": vector_payload.get("feature_count"),
            "algorithm": vector_payload.get("algorithm"),
        },
        "graph": {
            "node_count": graph_payload.get("node_count"),
            "edge_count": graph_payload.get("edge_count"),
        },
        "network_touched": False,
        "artifact_lifecycle": "temporary_deleted_after_run",
        "cases": case_reports,
    }


def run_live_search_eval_suite(
    run: str = "latest",
    suite_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> dict[str, object]:
    """Run a local retrieval eval against an already-built bounded live run."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_LIVE_SEARCH_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    roots = StorageRoots.from_env(root)
    artifacts = artifact_root or roots.artifact
    if artifacts is None:
        raise FileNotFoundError("CONNECTOR_ARTIFACT_ROOT is not configured")

    index_receipt = _load_latest_or_named_receipt(artifacts, run, "index")
    run_id = str(index_receipt.get("index_id") or index_receipt.get("run_id") or run)
    crawl_receipt = _load_latest_or_named_receipt(artifacts, run_id, "crawl")
    normalize_receipt = _load_latest_or_named_receipt(artifacts, run_id, "normalize")
    index_path = Path(str(index_receipt["index_path"]))
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    case_reports = [
        _run_live_search_case(case, index_path, int(suite.get("default_limit", 5)))
        for case in suite.get("cases", [])
    ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    crawl_counts = crawl_receipt.get("counts", {})
    normalize_counts = normalize_receipt.get("counts", {})
    policy = crawl_receipt.get("policy", {})
    checks = {
        "policy_preserved": policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False,
        "index_has_posts": int(index_payload.get("doc_count", 0)) > 0,
        "network_limited_to_source_crawl": crawl_receipt.get("network_touched") is True
        and normalize_receipt.get("network_touched") is False
        and index_receipt.get("network_touched") is False,
    }
    status = "ok" if not failed and all(checks.values()) else "error"
    return {
        "schema": "aoa_4pda_live_search_eval_report_v1",
        "status": status,
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "run_id": run_id,
        "dataset": suite.get("dataset", {}),
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
            "requested_topics": int(crawl_counts.get("requested_topics", crawl_counts.get("requested", 0))),
            "requested_pages": int(crawl_counts.get("requested_pages", crawl_counts.get("requested", 0))),
            "fetched_topics": int(crawl_counts.get("fetched_topics", crawl_counts.get("fetched", 0))),
            "fetched_pages": int(crawl_counts.get("fetched_pages", crawl_counts.get("fetched", 0))),
            "normalized_topics": int(normalize_counts.get("topics", 0)),
            "normalized_pages": int(normalize_counts.get("pages", normalize_counts.get("topics", 0))),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
            "path": str(index_path),
        },
        "checks": checks,
        "network_touched": False,
        "source_run_network_touched": bool(crawl_receipt.get("network_touched")),
        "artifact_lifecycle": "read_existing_configured_storage",
        "cases": case_reports,
    }


def run_live_graph_query_eval_suite(
    run: str = "latest",
    suite_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> dict[str, object]:
    """Run graph-query evals against an already-built bounded live run."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_LIVE_GRAPH_QUERY_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    roots = StorageRoots.from_env(root)
    artifacts = artifact_root or roots.artifact
    if artifacts is None:
        raise FileNotFoundError("CONNECTOR_ARTIFACT_ROOT is not configured")

    index_receipt = _load_latest_or_named_receipt(artifacts, run, "index")
    run_id = str(index_receipt.get("index_id") or index_receipt.get("run_id") or run)
    crawl_receipt = _load_latest_or_named_receipt(artifacts, run_id, "crawl")
    normalize_receipt = _load_latest_or_named_receipt(artifacts, run_id, "normalize")
    graph_receipt = _load_latest_or_named_receipt(artifacts, run_id, "graph")
    index_path = Path(str(index_receipt["index_path"]))
    graph_path = Path(str(graph_receipt["graph_path"]))
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
    case_reports = [
        _run_live_graph_query_case(case, index_path, graph_path, int(suite.get("default_limit", 5)))
        for case in suite.get("cases", [])
    ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    crawl_counts = crawl_receipt.get("counts", {})
    normalize_counts = normalize_receipt.get("counts", {})
    policy = crawl_receipt.get("policy", {})
    dataset = suite.get("dataset", {})
    expected_profile = dataset.get("expected_profile")
    checks = {
        "policy_preserved": policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False,
        "profile_matches": True
        if expected_profile is None
        else crawl_receipt.get("profile_id") == expected_profile
        and index_receipt.get("profile_id") == expected_profile
        and graph_receipt.get("profile_id") == expected_profile,
        "index_has_posts": int(index_payload.get("doc_count", 0)) > 0,
        "graph_has_relation_edges": bool(
            {
                edge.get("kind")
                for edge in graph_payload.get("edges", [])
                if str(edge.get("kind", "")).endswith(("_targets_file", "_uses_tool", "_mentions_firmware"))
            }
        ),
        "network_limited_to_source_crawl": crawl_receipt.get("network_touched") is True
        and normalize_receipt.get("network_touched") is False
        and index_receipt.get("network_touched") is False
        and graph_receipt.get("network_touched") is False,
    }
    status = "ok" if not failed and all(checks.values()) else "error"
    return {
        "schema": "aoa_4pda_live_graph_query_eval_report_v1",
        "status": status,
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "run_id": run_id,
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
            "requested_topics": int(crawl_counts.get("requested_topics", crawl_counts.get("requested", 0))),
            "requested_pages": int(crawl_counts.get("requested_pages", crawl_counts.get("requested", 0))),
            "fetched_topics": int(crawl_counts.get("fetched_topics", crawl_counts.get("fetched", 0))),
            "fetched_pages": int(crawl_counts.get("fetched_pages", crawl_counts.get("fetched", 0))),
            "normalized_topics": int(normalize_counts.get("topics", 0)),
            "normalized_pages": int(normalize_counts.get("pages", normalize_counts.get("topics", 0))),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
            "path": str(index_path),
        },
        "graph": {
            "node_count": graph_payload.get("node_count"),
            "edge_count": graph_payload.get("edge_count"),
            "path": str(graph_path),
        },
        "checks": checks,
        "network_touched": False,
        "source_run_network_touched": bool(crawl_receipt.get("network_touched")),
        "artifact_lifecycle": "read_existing_configured_storage",
        "cases": case_reports,
    }


def run_live_hybrid_query_eval_suite(
    run: str = "latest",
    suite_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> dict[str, object]:
    """Run hybrid query evals against an already-built bounded live run."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_LIVE_HYBRID_QUERY_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    roots = StorageRoots.from_env(root)
    artifacts = artifact_root or roots.artifact
    if artifacts is None:
        raise FileNotFoundError("CONNECTOR_ARTIFACT_ROOT is not configured")

    index_receipt = _load_latest_or_named_receipt(artifacts, run, "index")
    run_id = str(index_receipt.get("index_id") or index_receipt.get("run_id") or run)
    crawl_receipt = _load_latest_or_named_receipt(artifacts, run_id, "crawl")
    normalize_receipt = _load_latest_or_named_receipt(artifacts, run_id, "normalize")
    vector_receipt = _load_latest_or_named_receipt(artifacts, run_id, "vector")
    graph_receipt = _load_latest_or_named_receipt(artifacts, run_id, "graph")
    index_path = Path(str(index_receipt["index_path"]))
    vector_path = Path(str(vector_receipt["vector_path"]))
    graph_path = Path(str(graph_receipt["graph_path"]))
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    vector_payload = json.loads(vector_path.read_text(encoding="utf-8"))
    graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
    case_reports = [
        _run_live_hybrid_query_case(case, index_path, vector_path, graph_path, int(suite.get("default_limit", 5)))
        for case in suite.get("cases", [])
    ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    crawl_counts = crawl_receipt.get("counts", {})
    normalize_counts = normalize_receipt.get("counts", {})
    policy = crawl_receipt.get("policy", {})
    dataset = suite.get("dataset", {})
    expected_profile = dataset.get("expected_profile")
    checks = {
        "policy_preserved": policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False,
        "profile_matches": True
        if expected_profile is None
        else crawl_receipt.get("profile_id") == expected_profile
        and index_receipt.get("profile_id") == expected_profile
        and vector_receipt.get("profile_id") == expected_profile
        and graph_receipt.get("profile_id") == expected_profile,
        "index_has_posts": int(index_payload.get("doc_count", 0)) > 0,
        "vector_has_docs": int(vector_payload.get("doc_count", 0)) > 0,
        "graph_has_edges": int(graph_payload.get("edge_count", 0)) > 0,
        "network_limited_to_source_crawl": crawl_receipt.get("network_touched") is True
        and normalize_receipt.get("network_touched") is False
        and index_receipt.get("network_touched") is False
        and vector_receipt.get("network_touched") is False
        and graph_receipt.get("network_touched") is False,
    }
    status = "ok" if not failed and all(checks.values()) else "error"
    return {
        "schema": "aoa_4pda_live_hybrid_query_eval_report_v1",
        "status": status,
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "run_id": run_id,
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
            "requested_topics": int(crawl_counts.get("requested_topics", crawl_counts.get("requested", 0))),
            "requested_pages": int(crawl_counts.get("requested_pages", crawl_counts.get("requested", 0))),
            "fetched_topics": int(crawl_counts.get("fetched_topics", crawl_counts.get("fetched", 0))),
            "fetched_pages": int(crawl_counts.get("fetched_pages", crawl_counts.get("fetched", 0))),
            "normalized_topics": int(normalize_counts.get("topics", 0)),
            "normalized_pages": int(normalize_counts.get("pages", normalize_counts.get("topics", 0))),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
            "path": str(index_path),
        },
        "vector": {
            "unit": vector_payload.get("unit"),
            "doc_count": vector_payload.get("doc_count"),
            "feature_count": vector_payload.get("feature_count"),
            "algorithm": vector_payload.get("algorithm"),
            "path": str(vector_path),
        },
        "graph": {
            "node_count": graph_payload.get("node_count"),
            "edge_count": graph_payload.get("edge_count"),
            "path": str(graph_path),
        },
        "checks": checks,
        "network_touched": False,
        "source_run_network_touched": bool(crawl_receipt.get("network_touched")),
        "artifact_lifecycle": "read_existing_configured_storage",
        "cases": case_reports,
    }


def run_live_answer_eval_suite(
    run: str = "latest",
    suite_path: Path | None = None,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> dict[str, object]:
    """Run rendered-answer evals against an already-built bounded live run."""

    root = find_repo_root(repo_root)
    path = _resolve_repo_path(root, suite_path or DEFAULT_LIVE_ANSWER_EVAL_SUITE)
    suite = json.loads(path.read_text(encoding="utf-8"))
    roots = StorageRoots.from_env(root)
    artifacts = artifact_root or roots.artifact
    if artifacts is None:
        raise FileNotFoundError("CONNECTOR_ARTIFACT_ROOT is not configured")

    index_receipt = _load_latest_or_named_receipt(artifacts, run, "index")
    run_id = str(index_receipt.get("index_id") or index_receipt.get("run_id") or run)
    crawl_receipt = _load_latest_or_named_receipt(artifacts, run_id, "crawl")
    normalize_receipt = _load_latest_or_named_receipt(artifacts, run_id, "normalize")
    graph_receipt = _load_latest_or_named_receipt(artifacts, run_id, "graph")
    index_path = Path(str(index_receipt["index_path"]))
    graph_path = Path(str(graph_receipt["graph_path"]))
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
    case_reports = [
        _run_live_answer_case(case, index_path, graph_path, int(suite.get("default_limit", 5)))
        for case in suite.get("cases", [])
    ]

    failed = [case for case in case_reports if case["status"] != "ok"]
    crawl_counts = crawl_receipt.get("counts", {})
    normalize_counts = normalize_receipt.get("counts", {})
    policy = crawl_receipt.get("policy", {})
    dataset = suite.get("dataset", {})
    expected_profile = dataset.get("expected_profile")
    checks = {
        "policy_preserved": policy.get("allowed_public_only") is True
        and policy.get("internal_search_used") is False
        and policy.get("attachments_downloaded") is False,
        "profile_matches": True
        if expected_profile is None
        else crawl_receipt.get("profile_id") == expected_profile
        and index_receipt.get("profile_id") == expected_profile
        and graph_receipt.get("profile_id") == expected_profile,
        "index_has_posts": int(index_payload.get("doc_count", 0)) > 0,
        "graph_has_relation_edges": bool(
            {
                edge.get("kind")
                for edge in graph_payload.get("edges", [])
                if str(edge.get("kind", "")).endswith(("_targets_file", "_uses_tool", "_mentions_firmware"))
            }
        ),
        "network_limited_to_source_crawl": crawl_receipt.get("network_touched") is True
        and normalize_receipt.get("network_touched") is False
        and index_receipt.get("network_touched") is False
        and graph_receipt.get("network_touched") is False,
    }
    status = "ok" if not failed and all(checks.values()) else "error"
    return {
        "schema": "aoa_4pda_live_answer_eval_report_v1",
        "status": status,
        "suite_id": suite.get("suite_id"),
        "suite_path": _display_suite_path(root, path),
        "run_id": run_id,
        "dataset": dataset,
        "owner_boundary": {
            "local_eval_port_owner": suite.get("owner_repo"),
            "proof_owner_repo": suite.get("proof_owner_repo"),
            "central_boundary": suite.get("central_boundary"),
        },
        "counts": {
            "cases": len(case_reports),
            "passed": len(case_reports) - len(failed),
            "failed": len(failed),
            "requested_topics": int(crawl_counts.get("requested_topics", crawl_counts.get("requested", 0))),
            "requested_pages": int(crawl_counts.get("requested_pages", crawl_counts.get("requested", 0))),
            "fetched_topics": int(crawl_counts.get("fetched_topics", crawl_counts.get("fetched", 0))),
            "fetched_pages": int(crawl_counts.get("fetched_pages", crawl_counts.get("fetched", 0))),
            "normalized_topics": int(normalize_counts.get("topics", 0)),
            "normalized_pages": int(normalize_counts.get("pages", normalize_counts.get("topics", 0))),
        },
        "index": {
            "unit": index_payload.get("unit"),
            "doc_count": index_payload.get("doc_count"),
            "term_count": index_payload.get("term_count"),
            "path": str(index_path),
        },
        "graph": {
            "node_count": graph_payload.get("node_count"),
            "edge_count": graph_payload.get("edge_count"),
            "path": str(graph_path),
        },
        "checks": checks,
        "network_touched": False,
        "source_run_network_touched": bool(crawl_receipt.get("network_touched")),
        "artifact_lifecycle": "read_existing_configured_storage",
        "cases": case_reports,
    }


def _run_case(case: dict[str, object], index_path: Path) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    packet = query_keyword_index(index_path, query, limit=3)
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    evidence_refs = [str(ref) for ref in top_result.get("evidence_refs", [])]
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": top_result.get("post_id") == expect.get("top_post_id"),
        "top_chunk_ref_prefix": _any_prefix(evidence_refs, str(expect.get("top_chunk_ref_prefix", ""))),
        "matched_terms_any": _any_expected(expect.get("matched_terms_any", []), top_result.get("matched_terms", [])),
        "matched_exact_terms_any": _any_expected(
            expect.get("matched_exact_terms_any", []),
            top_result.get("matched_exact_terms", []),
        ),
        "query_report_technical_terms_all": _optional_all_expected(
            expect.get("query_report_technical_terms_all"),
            packet.get("query_report", {}).get("technical_terms", []),
        ),
        "source_url_contains": str(expect.get("source_url_contains", "")) in str(top_result.get("source_url", "")),
        "query_report_unit": packet.get("query_report", {}).get("unit") == expect.get("query_report_unit"),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "top_result": top_result,
    }


def _run_live_search_case(case: dict[str, object], index_path: Path, default_limit: int) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    limit = int(case.get("limit", default_limit))
    packet = query_keyword_index(index_path, query, limit=limit)
    results = packet.get("results", [])
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    evidence_refs = [str(ref) for ref in top_result.get("evidence_refs", [])]
    query_report = packet.get("query_report", {})
    expected_result_rank, expected_result = _find_expected_result(results, expect)
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": _optional_equal(top_result.get("post_id"), expect.get("top_post_id")),
        "top_chunk_ref_prefix": _optional_any_prefix(evidence_refs, expect.get("top_chunk_ref_prefix")),
        "matched_terms_any": _optional_any_expected(
            expect.get("matched_terms_any"),
            top_result.get("matched_terms", []),
        ),
        "matched_terms_all": _optional_all_expected(
            expect.get("matched_terms_all"),
            top_result.get("matched_terms", []),
        ),
        "matched_exact_terms_any": _optional_any_expected(
            expect.get("matched_exact_terms_any"),
            top_result.get("matched_exact_terms", []),
        ),
        "matched_specific_terms_any": _optional_any_expected(
            expect.get("matched_specific_terms_any"),
            top_result.get("matched_specific_terms", []),
        ),
        "matched_specific_terms_all": _optional_all_expected(
            expect.get("matched_specific_terms_all"),
            top_result.get("matched_specific_terms", []),
        ),
        "query_report_specific_terms_all": _optional_all_expected(
            expect.get("query_report_specific_terms_all"),
            query_report.get("specific_terms", []),
        ),
        "query_report_technical_terms_all": _optional_all_expected(
            expect.get("query_report_technical_terms_all"),
            query_report.get("technical_terms", []),
        ),
        "expected_result_present": _optional_expected_result_present(expected_result, expect),
        "expected_result_rank_max": _optional_rank_at_most(
            expected_result_rank,
            expect.get("expected_result_rank_max"),
        ),
        "expected_result_matched_terms_any": _optional_any_expected(
            expect.get("expected_result_matched_terms_any"),
            expected_result.get("matched_terms", []),
        ),
        "expected_result_matched_terms_all": _optional_all_expected(
            expect.get("expected_result_matched_terms_all"),
            expected_result.get("matched_terms", []),
        ),
        "expected_result_matched_specific_terms_any": _optional_any_expected(
            expect.get("expected_result_matched_specific_terms_any"),
            expected_result.get("matched_specific_terms", []),
        ),
        "expected_result_matched_specific_terms_all": _optional_all_expected(
            expect.get("expected_result_matched_specific_terms_all"),
            expected_result.get("matched_specific_terms", []),
        ),
        "source_url_contains": _optional_contains(top_result.get("source_url"), expect.get("source_url_contains")),
        "query_report_unit": _optional_equal(query_report.get("unit"), expect.get("query_report_unit")),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "query_report": query_report,
        "top_result": top_result,
        "expected_result_rank": expected_result_rank,
        "expected_result": _compact_ranked_result(expected_result_rank, expected_result),
        "diagnostics": _live_search_diagnostics(checks, top_result, expected_result_rank, expected_result, query_report),
    }


def _run_graph_case(case: dict[str, object], graph: dict[str, object]) -> dict[str, object]:
    expect = case.get("expect", {})
    post_id = str(expect.get("post_id", ""))
    topic_id = str(expect.get("topic_id", ""))
    post_node = f"post:{post_id}"
    topic_node = f"topic:{topic_id}"
    expected_entity_ids = [str(node_id) for node_id in expect.get("entity_node_ids", [])]
    expected_mention_ids = [str(node_id) for node_id in expect.get("post_mentions_entity_node_ids", [])]
    expected_relation_edges = [
        {
            "kind": str(edge.get("kind", "")),
            "from_node": str(edge.get("from_node", "")),
            "to_node": str(edge.get("to_node", "")),
        }
        for edge in expect.get("relation_edges", [])
    ]
    source_url_contains = str(expect.get("source_url_contains", ""))

    nodes = {str(node.get("node_id")): node for node in graph.get("nodes", [])}
    edges = [edge for edge in graph.get("edges", [])]
    post_mention_targets = {
        str(edge.get("to_node"))
        for edge in edges
        if edge.get("kind") == "post_mentions_entity" and edge.get("from_node") == post_node
    }
    expected_mention_edges = [
        edge
        for edge in edges
        if edge.get("kind") == "post_mentions_entity"
        and edge.get("from_node") == post_node
        and edge.get("to_node") in expected_mention_ids
    ]

    checks = {
        "post_node_present": post_node in nodes,
        "topic_contains_post_edge": _edge_exists(edges, "topic_contains_post", topic_node, post_node),
        "expected_entity_nodes_present": all(node_id in nodes for node_id in expected_entity_ids),
        "post_mentions_expected_entities": all(node_id in post_mention_targets for node_id in expected_mention_ids),
        "expected_relation_edges_present": all(_edge_exists(edges, **edge) for edge in expected_relation_edges),
        "source_refs_preserved": _source_refs_contain(nodes.get(post_node, {}), source_url_contains)
        and all(_source_refs_contain(edge, source_url_contains) for edge in expected_mention_edges)
        and all(
            _source_refs_contain(_find_edge(edges, **edge), source_url_contains)
            for edge in expected_relation_edges
        ),
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "post_node": post_node,
        "expected_entity_node_ids": expected_entity_ids,
        "expected_post_mentions_entity_node_ids": expected_mention_ids,
        "expected_relation_edges": expected_relation_edges,
        "checks": checks,
        "matched_entity_node_ids": sorted(node_id for node_id in expected_entity_ids if node_id in nodes),
        "matched_post_mentions_entity_node_ids": sorted(
            node_id
            for node_id in expected_mention_ids
            if node_id in post_mention_targets
        ),
        "matched_relation_edges": [
            edge
            for edge in expected_relation_edges
            if _edge_exists(edges, **edge)
        ],
    }


def _run_graph_query_case(case: dict[str, object], index_path: Path, graph_path: Path) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    packet = query_graph_packet(index_path, graph_path, query, limit=3)
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    context = top_result.get("graph_context", {}) if isinstance(top_result, dict) else {}
    relation_edges = context.get("relation_edges", []) if isinstance(context, dict) else []
    expected_relation_edges = [
        {
            "kind": str(edge.get("kind", "")),
            "from_node": str(edge.get("from_node", "")),
            "to_node": str(edge.get("to_node", "")),
        }
        for edge in expect.get("relation_edges", [])
    ]
    source_url_contains = str(expect.get("source_url_contains", ""))
    matched_relation_edges = [
        edge
        for edge in expected_relation_edges
        if _edge_exists(relation_edges, **edge)
    ]
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": top_result.get("post_id") == expect.get("top_post_id"),
        "graph_context_present": bool(context),
        "query_report_unit": packet.get("query_report", {}).get("unit") == expect.get("query_report_unit"),
        "expected_relation_edges_present": len(matched_relation_edges) == len(expected_relation_edges),
        "source_refs_preserved": str(source_url_contains) in str(top_result.get("source_url", ""))
        and all(
            _source_refs_contain(_find_edge(relation_edges, **edge), source_url_contains)
            for edge in expected_relation_edges
        ),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "top_result": top_result,
        "expected_relation_edges": expected_relation_edges,
        "matched_relation_edges": matched_relation_edges,
    }


def _run_hybrid_query_case(
    case: dict[str, object],
    index_path: Path,
    vector_path: Path,
    graph_path: Path,
) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    packet = query_hybrid_packet(index_path, vector_path, graph_path, query, limit=3)
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    context = top_result.get("graph_context", {}) if isinstance(top_result, dict) else {}
    breakdown = top_result.get("score_breakdown", {}) if isinstance(top_result, dict) else {}
    source_url_contains = str(expect.get("source_url_contains", ""))
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": top_result.get("post_id") == expect.get("top_post_id"),
        "hybrid_algorithm": packet.get("query_report", {}).get("algorithm") == expect.get("query_report_algorithm"),
        "query_report_unit": packet.get("query_report", {}).get("unit") == expect.get("query_report_unit"),
        "vector_score_present": float(breakdown.get("vector_raw") or 0.0) > 0,
        "keyword_score_present": float(breakdown.get("keyword_raw") or 0.0) > 0,
        "graph_context_present": bool(context),
        "source_refs_preserved": source_url_contains in str(top_result.get("source_url", "")),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "top_result": top_result,
        "hybrid_report": packet.get("hybrid_report", {}),
        "vector_report": packet.get("vector_report", {}),
    }


def _run_live_hybrid_query_case(
    case: dict[str, object],
    index_path: Path,
    vector_path: Path,
    graph_path: Path,
    default_limit: int,
) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    limit = int(case.get("limit", default_limit))
    packet = query_hybrid_packet(index_path, vector_path, graph_path, query, limit=limit)
    results = packet.get("results", [])
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    query_report = packet.get("query_report", {})
    hybrid_report = packet.get("hybrid_report", {})
    vector_report = packet.get("vector_report", {})
    expected_result_rank, expected_result = _find_expected_result(results, expect)
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": _optional_equal(top_result.get("post_id"), expect.get("top_post_id")),
        "top_keyword_score_present": _optional_score_component_positive(
            top_result,
            "keyword_raw",
            expect.get("top_keyword_score_present"),
        ),
        "top_vector_score_present": _optional_score_component_positive(
            top_result,
            "vector_raw",
            expect.get("top_vector_score_present"),
        ),
        "top_graph_score_present": _optional_score_component_positive(
            top_result,
            "graph_raw",
            expect.get("top_graph_score_present"),
        ),
        "top_graph_context_present": _optional_bool(
            bool(top_result.get("graph_context")),
            expect.get("top_graph_context_present"),
        ),
        "expected_result_present": _optional_expected_result_present(expected_result, expect),
        "expected_result_rank_max": _optional_rank_at_most(
            expected_result_rank,
            expect.get("expected_result_rank_max"),
        ),
        "expected_result_keyword_score_present": _optional_score_component_positive(
            expected_result,
            "keyword_raw",
            expect.get("expected_result_keyword_score_present"),
        ),
        "expected_result_vector_score_present": _optional_score_component_positive(
            expected_result,
            "vector_raw",
            expect.get("expected_result_vector_score_present"),
        ),
        "expected_result_graph_score_present": _optional_score_component_positive(
            expected_result,
            "graph_raw",
            expect.get("expected_result_graph_score_present"),
        ),
        "expected_result_matched_specific_terms_all": _optional_all_expected(
            expect.get("expected_result_matched_specific_terms_all"),
            expected_result.get("matched_specific_terms", []),
        ),
        "matched_specific_terms_all": _optional_all_expected(
            expect.get("matched_specific_terms_all"),
            top_result.get("matched_specific_terms", []),
        ),
        "source_url_contains": _optional_contains(top_result.get("source_url"), expect.get("source_url_contains")),
        "query_report_algorithm": _optional_equal(
            query_report.get("algorithm"),
            expect.get("query_report_algorithm"),
        ),
        "query_report_unit": _optional_equal(query_report.get("unit"), expect.get("query_report_unit")),
        "query_report_technical_terms_all": _optional_all_expected(
            expect.get("query_report_technical_terms_all"),
            query_report.get("technical_terms", []),
        ),
        "hybrid_report_algorithm": _optional_equal(
            hybrid_report.get("algorithm"),
            expect.get("hybrid_report_algorithm"),
        ),
        "vector_report_algorithm": _optional_equal(
            vector_report.get("algorithm"),
            expect.get("vector_report_algorithm"),
        ),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "query_report": query_report,
        "hybrid_report": hybrid_report,
        "vector_report": vector_report,
        "top_result": top_result,
        "expected_result_rank": expected_result_rank,
        "expected_result": _compact_ranked_result(expected_result_rank, expected_result),
        "diagnostics": _live_hybrid_diagnostics(checks, top_result, expected_result_rank, expected_result, query_report),
    }


def _run_live_graph_query_case(
    case: dict[str, object],
    index_path: Path,
    graph_path: Path,
    default_limit: int,
) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    limit = int(case.get("limit", default_limit))
    packet = query_graph_packet(index_path, graph_path, query, limit=limit)
    top_result = packet.get("results", [{}])[0] if packet.get("results") else {}
    context = top_result.get("graph_context", {}) if isinstance(top_result, dict) else {}
    relation_edges = context.get("relation_edges", []) if isinstance(context, dict) else []
    query_report = packet.get("query_report", {})
    graph_report = packet.get("graph_report", {})
    expected_relation_edges = [
        {
            "kind": str(edge.get("kind", "")),
            "from_node": str(edge.get("from_node", "")),
            "to_node": str(edge.get("to_node", "")),
        }
        for edge in expect.get("relation_edges", [])
    ]
    source_url_contains = expect.get("source_url_contains")
    matched_relation_edges = [
        edge
        for edge in expected_relation_edges
        if _edge_exists(relation_edges, **edge)
    ]
    checks = {
        "top_result_present": bool(top_result),
        "top_post_id": _optional_equal(top_result.get("post_id"), expect.get("top_post_id")),
        "graph_context_present": bool(context),
        "graph_report_relation_edge_kinds_all": _optional_all_expected(
            expect.get("graph_report_relation_edge_kinds_all"),
            graph_report.get("relation_edge_kinds", []),
        ),
        "graph_report_rerank_intents_all": _optional_all_expected(
            expect.get("graph_report_rerank_intents_all"),
            graph_report.get("rerank", {}).get("intents", []) if isinstance(graph_report.get("rerank"), dict) else [],
        ),
        "expected_relation_edges_present": len(matched_relation_edges) == len(expected_relation_edges),
        "matched_terms_any": _optional_any_expected(
            expect.get("matched_terms_any"),
            top_result.get("matched_terms", []),
        ),
        "matched_specific_terms_all": _optional_all_expected(
            expect.get("matched_specific_terms_all"),
            top_result.get("matched_specific_terms", []),
        ),
        "query_report_technical_terms_all": _optional_all_expected(
            expect.get("query_report_technical_terms_all"),
            query_report.get("technical_terms", []),
        ),
        "top_keyword_rank_min": _optional_minimum(
            int(top_result.get("keyword_rank", 0) or 0),
            expect.get("top_keyword_rank_min"),
        ),
        "source_url_contains": _optional_contains(top_result.get("source_url"), source_url_contains),
        "source_refs_preserved": True
        if source_url_contains is None
        else all(
            _source_refs_contain(_find_edge(relation_edges, **edge), str(source_url_contains))
            for edge in expected_relation_edges
        ),
        "query_report_unit": _optional_equal(query_report.get("unit"), expect.get("query_report_unit")),
        "internal_search_unused": packet.get("policy", {}).get("internal_search_used") is False,
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "query_report": query_report,
        "graph_report": graph_report,
        "top_result": top_result,
        "expected_relation_edges": expected_relation_edges,
        "matched_relation_edges": matched_relation_edges,
    }


def _run_answer_case(case: dict[str, object], index_path: Path, graph_path: Path) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    evidence_packet = query_graph_packet(index_path, graph_path, query, limit=3)
    answer_packet = render_answer_packet(evidence_packet, limit=3)
    top_answer = answer_packet.get("answers", [{}])[0] if answer_packet.get("answers") else {}
    checks = _answer_checks(top_answer, answer_packet, expect)
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "top_answer": top_answer,
        "expected": expect,
    }


def _run_live_answer_case(
    case: dict[str, object],
    index_path: Path,
    graph_path: Path,
    default_limit: int,
) -> dict[str, object]:
    query = str(case.get("query", ""))
    expect = case.get("expect", {})
    limit = int(case.get("limit", default_limit))
    evidence_packet = query_graph_packet(index_path, graph_path, query, limit=limit)
    answer_packet = render_answer_packet(evidence_packet, limit=limit)
    top_result = evidence_packet.get("results", [{}])[0] if evidence_packet.get("results") else {}
    top_answer = answer_packet.get("answers", [{}])[0] if answer_packet.get("answers") else {}
    query_report = evidence_packet.get("query_report", {})
    graph_report = evidence_packet.get("graph_report", {})
    checks = {
        **_answer_checks(top_answer, answer_packet, expect),
        "matched_terms_any": _optional_any_expected(
            expect.get("matched_terms_any"),
            top_result.get("matched_terms", []),
        ),
        "matched_terms_all": _optional_all_expected(
            expect.get("matched_terms_all"),
            top_result.get("matched_terms", []),
        ),
        "matched_exact_terms_any": _optional_any_expected(
            expect.get("matched_exact_terms_any"),
            top_result.get("matched_exact_terms", []),
        ),
        "matched_specific_terms_all": _optional_all_expected(
            expect.get("matched_specific_terms_all"),
            top_result.get("matched_specific_terms", []),
        ),
        "query_report_specific_terms_all": _optional_all_expected(
            expect.get("query_report_specific_terms_all"),
            query_report.get("specific_terms", []),
        ),
        "query_report_technical_terms_all": _optional_all_expected(
            expect.get("query_report_technical_terms_all"),
            query_report.get("technical_terms", []),
        ),
        "answer_context_labels_min": _optional_minimum(
            _answer_context_label_count(top_answer),
            expect.get("answer_context_labels_min"),
        ),
        "query_report_unit": _optional_equal(query_report.get("unit"), expect.get("query_report_unit")),
        "graph_report_relation_edge_kinds_all": _optional_all_expected(
            expect.get("graph_report_relation_edge_kinds_all"),
            graph_report.get("relation_edge_kinds", []),
        ),
        "graph_report_rerank_intents_all": _optional_all_expected(
            expect.get("graph_report_rerank_intents_all"),
            graph_report.get("rerank", {}).get("intents", []) if isinstance(graph_report.get("rerank"), dict) else [],
        ),
        "top_keyword_rank_min": _optional_minimum(
            int(top_result.get("keyword_rank", 0) or 0),
            expect.get("top_keyword_rank_min"),
        ),
    }
    return {
        "case_id": case.get("case_id"),
        "status": "ok" if all(checks.values()) else "error",
        "query": query,
        "checks": checks,
        "query_report": query_report,
        "graph_report": graph_report,
        "answer_report": answer_packet.get("answer_report", {}),
        "diagnostics": _live_answer_diagnostics(checks, top_result, top_answer, query_report),
        "top_evidence_result": _compact_top_result(top_result),
        "top_answer": top_answer,
        "expected": expect,
    }


def _answer_checks(
    top_answer: dict[str, object],
    answer_packet: dict[str, object],
    expect: object,
) -> dict[str, bool]:
    expected = expect if isinstance(expect, dict) else {}
    source_url_contains = expected.get("source_url_contains")
    freshness = top_answer.get("freshness", {})
    if not isinstance(freshness, dict):
        freshness = {}
    label_fields = [
        "issue_labels",
        "fix_labels",
        "warning_labels",
        "warned_target_labels",
        "root_action_labels",
        "recovery_action_labels",
        "target_file_labels",
        "tool_labels",
        "firmware_context_labels",
    ]
    return {
        "top_answer_present": bool(top_answer),
        "top_post_id": _optional_equal(top_answer.get("post_id"), expected.get("top_post_id")),
        "answer_kind": _optional_equal(top_answer.get("answer_kind"), expected.get("answer_kind")),
        "expected_labels_present": all(
            _optional_all_expected(expected.get(field), top_answer.get(field, []))
            for field in label_fields
        ),
        "answer_text_contains": all(
            str(fragment) in str(top_answer.get("answer_text", ""))
            for fragment in _list_or_empty(expected.get("answer_text_contains"))
        ),
        "source_refs_preserved": True
        if source_url_contains is None
        else str(source_url_contains) in str(top_answer.get("source_url", ""))
        and _any_source_ref_contains(top_answer.get("source_refs", []), str(source_url_contains)),
        "freshness_present": bool(freshness),
        "freshness_note_present": bool(str(freshness.get("note", "")).strip()),
        "internal_search_unused": answer_packet.get("policy", {}).get("internal_search_used") is False,
    }


def _resolve_repo_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_suite_path(repo_root: Path, path: Path) -> str:
    return str(path.relative_to(repo_root)) if path.is_relative_to(repo_root) else str(path)


def _load_latest_or_named_receipt(artifact_root: Path, run: str, kind: str) -> dict[str, object]:
    receipt_dir = artifact_root / "receipts"
    path = receipt_dir / f"latest_{kind}.json" if run == "latest" else receipt_dir / f"{run}.{kind}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _any_prefix(values: list[str], prefix: str) -> bool:
    return bool(prefix) and any(value.startswith(prefix) for value in values)


def _any_expected(expected: object, actual: object) -> bool:
    expected_values = {str(item).lower() for item in expected if str(item)}
    actual_values = {str(item).lower() for item in actual}
    return bool(expected_values.intersection(actual_values))


def _all_expected(expected: object, actual: object) -> bool:
    expected_values = {str(item).lower() for item in expected if str(item)}
    actual_values = {str(item).lower() for item in actual}
    return expected_values.issubset(actual_values)


def _optional_equal(actual: object, expected: object) -> bool:
    return True if expected is None else actual == expected


def _optional_contains(actual: object, expected: object) -> bool:
    return True if expected is None else str(expected) in str(actual)


def _optional_any_prefix(values: list[str], prefix: object) -> bool:
    return True if prefix is None else _any_prefix(values, str(prefix))


def _optional_any_expected(expected: object, actual: object) -> bool:
    return True if expected is None else _any_expected(expected, actual)


def _optional_all_expected(expected: object, actual: object) -> bool:
    return True if expected is None else _all_expected(expected, actual)


def _optional_minimum(actual: int, expected: object) -> bool:
    if expected is None:
        return True
    try:
        return actual >= int(expected)
    except (TypeError, ValueError):
        return False


def _optional_bool(actual: bool, expected: object) -> bool:
    return True if expected is None else actual is bool(expected)


def _optional_rank_at_most(actual_rank: int | None, expected: object) -> bool:
    if expected is None:
        return True
    if actual_rank is None:
        return False
    try:
        return actual_rank <= int(expected)
    except (TypeError, ValueError):
        return False


def _optional_expected_result_present(expected_result: dict[str, object], expect: object) -> bool:
    if not isinstance(expect, dict):
        return True
    if expect.get("expected_result_post_id") is None and expect.get("expected_result_source_url_contains") is None:
        return True
    return bool(expected_result)


def _optional_score_component_positive(result: object, component: str, expected: object) -> bool:
    if expected is None:
        return True
    return _score_component_positive(result, component) is bool(expected)


def _score_component_positive(result: object, component: str) -> bool:
    if not isinstance(result, dict):
        return False
    breakdown = result.get("score_breakdown", {})
    if not isinstance(breakdown, dict):
        return False
    try:
        return float(breakdown.get(component) or 0.0) > 0.0
    except (TypeError, ValueError):
        return False


def _list_or_empty(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _find_expected_result(results: object, expect: object) -> tuple[int | None, dict[str, object]]:
    if not isinstance(results, list) or not isinstance(expect, dict):
        return None, {}
    expected_post_id = expect.get("expected_result_post_id")
    expected_source_url = expect.get("expected_result_source_url_contains")
    if expected_post_id is None and expected_source_url is None:
        return None, {}
    for rank, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            continue
        if expected_post_id is not None and str(result.get("post_id")) != str(expected_post_id):
            continue
        if expected_source_url is not None and str(expected_source_url) not in str(result.get("source_url", "")):
            continue
        return rank, result
    return None, {}


def _answer_context_label_count(answer: dict[str, object]) -> int:
    fields = [
        "issue_labels",
        "fix_labels",
        "warning_labels",
        "warned_target_labels",
        "root_action_labels",
        "recovery_action_labels",
        "target_file_labels",
        "tool_labels",
        "firmware_context_labels",
    ]
    return sum(len(answer.get(field, [])) for field in fields if isinstance(answer.get(field), list))


def _compact_top_result(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        return {}
    context = result.get("graph_context", {})
    relation_edges = context.get("relation_edges", []) if isinstance(context, dict) else []
    return {
        "source_url": result.get("source_url"),
        "topic_id": result.get("topic_id"),
        "post_id": result.get("post_id"),
        "chunk_id": result.get("chunk_id"),
        "keyword_rank": result.get("keyword_rank"),
        "vector_rank": result.get("vector_rank"),
        "graph_rank": result.get("graph_rank"),
        "hybrid_rank": result.get("hybrid_rank"),
        "score": result.get("score"),
        "score_breakdown": result.get("score_breakdown", {}),
        "relation_rerank": result.get("relation_rerank", {}),
        "matched_terms": result.get("matched_terms", []),
        "matched_exact_terms": result.get("matched_exact_terms", []),
        "matched_specific_terms": result.get("matched_specific_terms", []),
        "matched_phrases": result.get("matched_phrases", []),
        "evidence_refs": result.get("evidence_refs", []),
        "graph_relation_edges": [
            {
                "kind": edge.get("kind"),
                "from_node": edge.get("from_node"),
                "to_node": edge.get("to_node"),
                "confidence": edge.get("confidence"),
            }
            for edge in relation_edges
            if isinstance(edge, dict)
        ],
    }


def _compact_ranked_result(rank: int | None, result: object) -> dict[str, object]:
    compact = _compact_top_result(result)
    if compact:
        compact["rank"] = rank
    return compact


def _live_search_diagnostics(
    checks: dict[str, bool],
    top_result: object,
    expected_result_rank: int | None,
    expected_result: object,
    query_report: object,
) -> dict[str, object]:
    report = query_report if isinstance(query_report, dict) else {}
    return {
        "failed_checks": sorted(name for name, ok in checks.items() if not ok),
        "query_terms": report.get("terms", []),
        "query_exact_terms": report.get("exact_terms", []),
        "query_specific_terms": report.get("specific_terms", []),
        "query_technical_terms": report.get("technical_terms", []),
        "top_result": _compact_top_result(top_result),
        "expected_result": _compact_ranked_result(expected_result_rank, expected_result),
    }


def _live_answer_diagnostics(
    checks: dict[str, bool],
    top_result: object,
    top_answer: dict[str, object],
    query_report: object,
) -> dict[str, object]:
    report = query_report if isinstance(query_report, dict) else {}
    compact_result = _compact_top_result(top_result)
    label_fields = [
        "issue_labels",
        "fix_labels",
        "warning_labels",
        "warned_target_labels",
        "root_action_labels",
        "recovery_action_labels",
        "target_file_labels",
        "tool_labels",
        "firmware_context_labels",
    ]
    return {
        "failed_checks": sorted(name for name, ok in checks.items() if not ok),
        "query_terms": report.get("terms", []),
        "query_exact_terms": report.get("exact_terms", []),
        "query_specific_terms": report.get("specific_terms", []),
        "query_technical_terms": report.get("technical_terms", []),
        "top_result_score": compact_result.get("score"),
        "top_result_score_breakdown": compact_result.get("score_breakdown", {}),
        "top_result_matches": {
            "matched_terms": compact_result.get("matched_terms", []),
            "matched_exact_terms": compact_result.get("matched_exact_terms", []),
            "matched_specific_terms": compact_result.get("matched_specific_terms", []),
            "matched_phrases": compact_result.get("matched_phrases", []),
        },
        "answer_context": {
            "answer_kind": top_answer.get("answer_kind"),
            "label_count": _answer_context_label_count(top_answer),
            "label_counts": {
                field: len(top_answer.get(field, []))
                for field in label_fields
                if isinstance(top_answer.get(field), list)
            },
            "relation_confidence_min": top_answer.get("confidence", {}).get("relation_confidence_min")
            if isinstance(top_answer.get("confidence"), dict)
            else None,
        },
        "freshness": top_answer.get("freshness", {}),
        "graph_relation_edges": compact_result.get("graph_relation_edges", []),
    }


def _live_hybrid_diagnostics(
    checks: dict[str, bool],
    top_result: object,
    expected_result_rank: int | None,
    expected_result: object,
    query_report: object,
) -> dict[str, object]:
    report = query_report if isinstance(query_report, dict) else {}
    return {
        "failed_checks": sorted(name for name, ok in checks.items() if not ok),
        "query_terms": report.get("terms", []),
        "query_exact_terms": report.get("exact_terms", []),
        "query_specific_terms": report.get("specific_terms", []),
        "query_technical_terms": report.get("technical_terms", []),
        "top_result": _compact_top_result(top_result),
        "expected_result": _compact_ranked_result(expected_result_rank, expected_result),
    }


def _any_source_ref_contains(values: object, needle: str) -> bool:
    if not isinstance(values, list):
        return False
    return bool(needle) and any(needle in str(value) for value in values)


def _edge_exists(edges: list[dict[str, object]], kind: str, from_node: str, to_node: str) -> bool:
    return bool(_find_edge(edges, kind, from_node, to_node))


def _find_edge(edges: list[dict[str, object]], kind: str, from_node: str, to_node: str) -> dict[str, object]:
    return next(
        (
            edge
            for edge in edges
            if edge.get("kind") == kind
            and edge.get("from_node") == from_node
            and edge.get("to_node") == to_node
        ),
        {},
    )


def _source_refs_contain(item: dict[str, object], needle: str) -> bool:
    refs = [str(ref) for ref in item.get("source_refs", [])]
    return bool(needle) and any(needle in ref for ref in refs)
