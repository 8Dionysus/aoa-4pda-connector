"""Local eval runners for connector-owned retrieval checks."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from aoa_4pda_connector.config import find_repo_root
from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.query import query_graph_packet, query_keyword_index


DEFAULT_SEARCH_EVAL_SUITE = Path("evals/suites/starter_search_quality.json")
DEFAULT_GRAPH_EVAL_SUITE = Path("evals/suites/starter_graph_relations.json")
DEFAULT_GRAPH_QUERY_EVAL_SUITE = Path("evals/suites/starter_graph_query_packets.json")


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
        "suite_path": str(path.relative_to(root)),
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
        "suite_path": str(path.relative_to(root)),
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
        "suite_path": str(path.relative_to(root)),
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


def _resolve_repo_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _any_prefix(values: list[str], prefix: str) -> bool:
    return bool(prefix) and any(value.startswith(prefix) for value in values)


def _any_expected(expected: object, actual: object) -> bool:
    expected_values = {str(item).lower() for item in expected if str(item)}
    actual_values = {str(item).lower() for item in actual}
    return bool(expected_values.intersection(actual_values))


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
