from __future__ import annotations

from pathlib import Path

from aoa_4pda_connector.evaluation import (
    run_answer_eval_suite,
    run_graph_eval_suite,
    run_graph_query_eval_suite,
    run_search_eval_suite,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_search_eval_suite_reports_case_quality_without_network():
    report = run_search_eval_suite(REPO_ROOT / "evals/suites/starter_search_quality.json", REPO_ROOT)

    assert report["schema"] == "aoa_4pda_search_eval_report_v1"
    assert report["suite_id"] == "starter-search-quality"
    assert report["status"] == "ok"
    assert report["network_touched"] is False
    assert report["artifact_lifecycle"] == "temporary_deleted_after_run"
    assert report["owner_boundary"]["local_eval_port_owner"] == "aoa-4pda-connector"
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["counts"] == {"cases": 2, "passed": 2, "failed": 0}

    bootloop_case = report["cases"][0]
    assert bootloop_case["case_id"] == "bootloop-fix-post"
    assert bootloop_case["status"] == "ok"
    assert bootloop_case["top_result"]["post_id"] == "1002"
    assert bootloop_case["checks"]["top_chunk_ref_prefix"] is True
    assert bootloop_case["checks"]["query_report_unit"] is True
    assert bootloop_case["checks"]["internal_search_unused"] is True


def test_graph_eval_suite_reports_live_shape_entity_edges_without_network():
    report = run_graph_eval_suite(REPO_ROOT / "evals/suites/starter_graph_relations.json", REPO_ROOT)

    assert report["schema"] == "aoa_4pda_graph_eval_report_v1"
    assert report["suite_id"] == "starter-graph-relations"
    assert report["status"] == "ok"
    assert report["network_touched"] is False
    assert report["artifact_lifecycle"] == "temporary_deleted_after_run"
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["counts"] == {"cases": 1, "passed": 1, "failed": 0}

    case = report["cases"][0]
    assert case["case_id"] == "live-shape-issue-fix-warning-post"
    assert case["status"] == "ok"
    assert case["checks"]["post_node_present"] is True
    assert case["checks"]["topic_contains_post_edge"] is True
    assert case["checks"]["expected_entity_nodes_present"] is True
    assert case["checks"]["post_mentions_expected_entities"] is True
    assert case["checks"]["expected_relation_edges_present"] is True
    assert case["checks"]["source_refs_preserved"] is True


def test_graph_query_eval_suite_reports_relation_context_without_network():
    report = run_graph_query_eval_suite(REPO_ROOT / "evals/suites/starter_graph_query_packets.json", REPO_ROOT)

    assert report["schema"] == "aoa_4pda_graph_query_eval_report_v1"
    assert report["suite_id"] == "starter-graph-query-packets"
    assert report["status"] == "ok"
    assert report["network_touched"] is False
    assert report["artifact_lifecycle"] == "temporary_deleted_after_run"
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["counts"] == {"cases": 1, "passed": 1, "failed": 0}

    case = report["cases"][0]
    assert case["case_id"] == "bootloop-relation-context-packet"
    assert case["status"] == "ok"
    assert case["checks"]["top_post_id"] is True
    assert case["checks"]["graph_context_present"] is True
    assert case["checks"]["expected_relation_edges_present"] is True
    assert case["checks"]["source_refs_preserved"] is True
    assert case["checks"]["internal_search_unused"] is True


def test_answer_eval_suite_reports_rendered_answer_without_network():
    report = run_answer_eval_suite(REPO_ROOT / "evals/suites/starter_answer_packets.json", REPO_ROOT)

    assert report["schema"] == "aoa_4pda_answer_eval_report_v1"
    assert report["suite_id"] == "starter-answer-packets"
    assert report["status"] == "ok"
    assert report["network_touched"] is False
    assert report["artifact_lifecycle"] == "temporary_deleted_after_run"
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["counts"] == {"cases": 1, "passed": 1, "failed": 0}

    case = report["cases"][0]
    assert case["case_id"] == "bootloop-answer-packet"
    assert case["status"] == "ok"
    assert case["checks"]["top_answer_present"] is True
    assert case["checks"]["top_post_id"] is True
    assert case["checks"]["answer_kind"] is True
    assert case["checks"]["expected_labels_present"] is True
    assert case["checks"]["source_refs_preserved"] is True
    assert case["checks"]["internal_search_unused"] is True
