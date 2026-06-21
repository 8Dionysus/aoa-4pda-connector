from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.evaluation import (
    run_answer_eval_suite,
    run_graph_eval_suite,
    run_graph_query_eval_suite,
    run_live_answer_eval_suite,
    run_live_graph_query_eval_suite,
    run_live_search_eval_suite,
    run_search_eval_suite,
)
from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import extract_entities


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
    assert report["counts"] == {"cases": 4, "passed": 4, "failed": 0}

    bootloop_case = report["cases"][0]
    assert bootloop_case["case_id"] == "bootloop-fix-post"
    assert bootloop_case["status"] == "ok"
    assert bootloop_case["top_result"]["post_id"] == "1002"
    assert bootloop_case["checks"]["top_chunk_ref_prefix"] is True
    assert bootloop_case["checks"]["query_report_unit"] is True
    assert bootloop_case["checks"]["internal_search_unused"] is True
    split_version_case = next(case for case in report["cases"] if case["case_id"] == "split-firmware-version-post")
    assert split_version_case["checks"]["query_report_technical_terms_all"] is True
    assert split_version_case["top_result"]["post_id"] == "1001"


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
    assert case["checks"]["freshness_present"] is True
    assert case["checks"]["freshness_note_present"] is True
    assert case["checks"]["internal_search_unused"] is True


def test_xiaomi_answer_eval_suite_reports_root_recovery_context_without_network():
    report = run_answer_eval_suite(REPO_ROOT / "evals/suites/xiaomi_13t_answer_packets.json", REPO_ROOT)

    assert report["schema"] == "aoa_4pda_answer_eval_report_v1"
    assert report["suite_id"] == "xiaomi-13t-answer-packets"
    assert report["status"] == "ok"
    assert report["network_touched"] is False
    assert report["counts"] == {"cases": 1, "passed": 1, "failed": 0}

    case = report["cases"][0]
    assert case["case_id"] == "xiaomi-13t-root-recovery-answer-packet"
    assert case["status"] == "ok"
    assert case["checks"]["top_post_id"] is True
    assert case["checks"]["answer_kind"] is True
    assert case["checks"]["expected_labels_present"] is True
    assert case["checks"]["answer_text_contains"] is True
    assert case["checks"]["freshness_present"] is True
    assert case["checks"]["freshness_note_present"] is True
    assert case["top_answer"]["root_action_labels"] == ["patch boot.img"]
    assert case["top_answer"]["recovery_action_labels"] == ["flash recovery.img"]


def test_live_search_eval_suite_checks_named_run_without_network(tmp_path):
    run_id = "live-search-eval-test"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = tmp_path / "data" / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    _write_live_search_eval_topics(normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "cache" / "indexes" / run_id, "starter")
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    _write_receipt(
        receipts_dir,
        run_id,
        "crawl",
        {
            "schema": "aoa_4pda_crawl_receipt_v1",
            "run_id": run_id,
            "profile_id": "starter",
            "policy": {
                "allowed_public_only": True,
                "internal_search_used": False,
                "attachments_downloaded": False,
            },
            "counts": {
                "requested_topics": 2,
                "requested_pages": 2,
                "fetched_topics": 2,
                "fetched_pages": 2,
                "errors": 0,
            },
            "network_touched": True,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "normalize",
        {
            "schema": "aoa_4pda_normalize_receipt_v1",
            "run_id": run_id,
            "source_run_id": run_id,
            "counts": {"topics": 2, "pages": 2},
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "index",
        {
            "schema": "aoa_4pda_index_manifest_v1",
            "index_id": run_id,
            "profile_id": "starter",
            "source_run_ids": [run_id],
            "index_kinds": ["keyword"],
            "index_path": str(index_path),
            "network_touched": False,
        },
    )

    report = run_live_search_eval_suite(
        run_id,
        REPO_ROOT / "evals/suites/live_starter_search_quality.json",
        REPO_ROOT,
        artifact_root,
    )

    assert report["schema"] == "aoa_4pda_live_search_eval_report_v1"
    assert report["suite_id"] == "live-starter-search-quality"
    assert report["status"] == "ok"
    assert report["run_id"] == run_id
    assert report["network_touched"] is False
    assert report["source_run_network_touched"] is True
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["counts"]["cases"] == 4
    assert report["counts"]["failed"] == 0
    assert report["checks"]["policy_preserved"] is True
    assert report["checks"]["index_has_posts"] is True

    boot_case = report["cases"][0]
    assert boot_case["case_id"] == "redmi-note-10-pro-boot-image"
    assert boot_case["checks"]["top_post_id"] is True
    assert boot_case["checks"]["matched_specific_terms_any"] is True
    assert boot_case["checks"]["query_report_specific_terms_all"] is True
    sweet_case = next(case for case in report["cases"] if case["case_id"] == "sweet-split-boot-image")
    assert sweet_case["checks"]["top_post_id"] is True
    assert sweet_case["checks"]["query_report_technical_terms_all"] is True


def test_live_redmi_note_10_pro_search_eval_suite_checks_prepared_profile_without_network(tmp_path):
    run_id = "live-redmi-note-10-pro-eval-test"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = tmp_path / "data" / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    _write_live_search_eval_topics(normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "cache" / "indexes" / run_id, "redmi-note-10-pro")
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    _write_receipt(
        receipts_dir,
        run_id,
        "crawl",
        {
            "schema": "aoa_4pda_crawl_receipt_v1",
            "run_id": run_id,
            "profile_id": "redmi-note-10-pro",
            "policy": {
                "allowed_public_only": True,
                "internal_search_used": False,
                "attachments_downloaded": False,
            },
            "counts": {
                "requested_topics": 2,
                "requested_pages": 2,
                "fetched_topics": 2,
                "fetched_pages": 2,
                "errors": 0,
            },
            "network_touched": True,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "normalize",
        {
            "schema": "aoa_4pda_normalize_receipt_v1",
            "run_id": run_id,
            "source_run_id": run_id,
            "counts": {"topics": 2, "pages": 2},
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "index",
        {
            "schema": "aoa_4pda_index_manifest_v1",
            "index_id": run_id,
            "profile_id": "redmi-note-10-pro",
            "source_run_ids": [run_id],
            "index_kinds": ["keyword"],
            "index_path": str(index_path),
            "network_touched": False,
        },
    )

    report = run_live_search_eval_suite(
        run_id,
        REPO_ROOT / "evals/suites/live_redmi_note_10_pro_search_quality.json",
        REPO_ROOT,
        artifact_root,
    )

    assert report["schema"] == "aoa_4pda_live_search_eval_report_v1"
    assert report["suite_id"] == "live-redmi-note-10-pro-search-quality"
    assert report["status"] == "ok"
    assert report["run_id"] == run_id
    assert report["network_touched"] is False
    assert report["source_run_network_touched"] is True
    assert report["counts"]["cases"] == 3
    assert report["counts"]["passed"] == 3
    assert report["counts"]["failed"] == 0
    assert report["checks"]["policy_preserved"] is True

    sweet_case = next(case for case in report["cases"] if case["case_id"] == "redmi-note-10-pro-sweet-split-boot-image")
    assert sweet_case["checks"]["top_post_id"] is True
    assert sweet_case["checks"]["query_report_technical_terms_all"] is True
    recovery_case = next(case for case in report["cases"] if case["case_id"] == "redmi-note-10-pro-recovery-bootloop")
    assert recovery_case["checks"]["top_post_id"] is True
    assert recovery_case["checks"]["query_report_specific_terms_all"] is True


def test_live_search_eval_suite_reports_expected_result_rank_without_network(tmp_path):
    run_id = "live-ranking-pressure-test"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = tmp_path / "data" / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    _write_live_ranking_pressure_topics(normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "cache" / "indexes" / run_id, "xiaomi-13t")
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    _write_receipt(
        receipts_dir,
        run_id,
        "crawl",
        {
            "schema": "aoa_4pda_crawl_receipt_v1",
            "run_id": run_id,
            "profile_id": "xiaomi-13t",
            "policy": {
                "allowed_public_only": True,
                "internal_search_used": False,
                "attachments_downloaded": False,
            },
            "counts": {
                "requested_topics": 1,
                "requested_pages": 1,
                "fetched_topics": 1,
                "fetched_pages": 1,
                "errors": 0,
            },
            "network_touched": True,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "normalize",
        {
            "schema": "aoa_4pda_normalize_receipt_v1",
            "run_id": run_id,
            "source_run_id": run_id,
            "counts": {"topics": 1, "pages": 1},
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "index",
        {
            "schema": "aoa_4pda_index_manifest_v1",
            "index_id": run_id,
            "profile_id": "xiaomi-13t",
            "source_run_ids": [run_id],
            "index_kinds": ["keyword"],
            "index_path": str(index_path),
            "network_touched": False,
        },
    )
    suite_path = tmp_path / "ranking_pressure_suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "schema": "aoa_4pda_live_search_eval_suite_v1",
                "suite_id": "unit-ranking-pressure",
                "owner_repo": "aoa-4pda-connector",
                "proof_owner_repo": "aoa-evals",
                "central_boundary": "local unit suite only",
                "default_limit": 5,
                "dataset": {
                    "kind": "bounded_live_run_keyword_index",
                    "expected_profile": "xiaomi-13t",
                },
                "cases": [
                    {
                        "case_id": "recovery-rich-result-in-top-n",
                        "query": "OrangeFox TWRP Xiaomi 13T fastboot recovery",
                        "expect": {
                            "expected_result_post_id": "2002",
                            "expected_result_source_url_contains": "showtopic=1076859&st=0#entry2002",
                            "expected_result_rank_max": 2,
                            "expected_result_matched_specific_terms_all": ["twrp", "fastboot", "recovery"],
                            "query_report_unit": "chunk",
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = run_live_search_eval_suite(
        run_id,
        suite_path,
        REPO_ROOT,
        artifact_root,
    )

    assert report["schema"] == "aoa_4pda_live_search_eval_report_v1"
    assert report["suite_id"] == "unit-ranking-pressure"
    assert report["status"] == "ok"
    assert report["network_touched"] is False
    assert report["counts"]["failed"] == 0

    case = report["cases"][0]
    assert case["top_result"]["post_id"] == "2001"
    assert case["checks"]["expected_result_present"] is True
    assert case["checks"]["expected_result_rank_max"] is True
    assert case["checks"]["expected_result_matched_specific_terms_all"] is True
    assert case["expected_result_rank"] == 2
    assert case["expected_result"]["post_id"] == "2002"
    assert case["diagnostics"]["expected_result"]["rank"] == 2
    assert case["diagnostics"]["failed_checks"] == []


def test_live_graph_query_eval_suite_checks_named_run_without_network(tmp_path):
    run_id = "live-graph-query-eval-test"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = tmp_path / "data" / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    _write_live_graph_query_eval_topics(normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "cache" / "indexes" / run_id, "xiaomi-13t")
    graph_path = build_graph(normalized_dir, artifact_root / "graphs" / run_id, "xiaomi-13t")
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    _write_receipt(
        receipts_dir,
        run_id,
        "crawl",
        {
            "schema": "aoa_4pda_crawl_receipt_v1",
            "run_id": run_id,
            "profile_id": "xiaomi-13t",
            "policy": {
                "allowed_public_only": True,
                "internal_search_used": False,
                "attachments_downloaded": False,
            },
            "counts": {
                "requested_topics": 1,
                "requested_pages": 1,
                "fetched_topics": 1,
                "fetched_pages": 1,
                "errors": 0,
            },
            "network_touched": True,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "normalize",
        {
            "schema": "aoa_4pda_normalize_receipt_v1",
            "run_id": run_id,
            "source_run_id": run_id,
            "counts": {"topics": 1, "pages": 1},
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "index",
        {
            "schema": "aoa_4pda_index_manifest_v1",
            "index_id": run_id,
            "profile_id": "xiaomi-13t",
            "source_run_ids": [run_id],
            "index_kinds": ["keyword"],
            "index_path": str(index_path),
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "graph",
        {
            "schema": "aoa_4pda_graph_receipt_v1",
            "run_id": run_id,
            "profile_id": "xiaomi-13t",
            "graph_path": str(graph_path),
            "network_touched": False,
        },
    )
    suite_path = tmp_path / "live_graph_query_suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "schema": "aoa_4pda_live_graph_query_eval_suite_v1",
                "suite_id": "unit-live-graph-query-quality",
                "owner_repo": "aoa-4pda-connector",
                "proof_owner_repo": "aoa-evals",
                "central_boundary": "local unit suite only",
                "default_limit": 5,
                "dataset": {
                    "kind": "bounded_live_run_keyword_index_plus_graph",
                    "expected_profile": "xiaomi-13t",
                },
                "cases": [
                    {
                        "case_id": "recovery-graph-context",
                        "query": "Xiaomi 13T aristotle recovery.img fastboot",
                        "expect": {
                            "top_post_id": "128964413",
                            "matched_specific_terms_all": ["recovery.img"],
                            "query_report_technical_terms_all": ["recovery.img", "aristotle"],
                            "graph_report_rerank_intents_all": ["recovery"],
                            "graph_report_relation_edge_kinds_all": [
                                "recovery_targets_file",
                                "recovery_uses_tool",
                            ],
                            "source_url_contains": "showtopic=1076859&st=2140#entry128964413",
                            "query_report_unit": "chunk",
                            "relation_edges": [
                                {
                                    "kind": "recovery_targets_file",
                                    "from_node": "entity:recovery_action:flash recovery.img",
                                    "to_node": "entity:file:recovery.img",
                                },
                                {
                                    "kind": "recovery_uses_tool",
                                    "from_node": "entity:recovery_action:flash recovery.img",
                                    "to_node": "entity:tool:fastboot",
                                },
                            ],
                        },
                    },
                    {
                        "case_id": "root-graph-context",
                        "query": "2306EPN60G HyperOS boot.img Magisk KSU",
                        "expect": {
                            "top_post_id": "128449684",
                            "matched_specific_terms_all": ["boot.img", "magisk"],
                            "graph_report_rerank_intents_all": ["root"],
                            "graph_report_relation_edge_kinds_all": [
                                "root_targets_file",
                                "root_uses_tool",
                            ],
                            "source_url_contains": "showtopic=1076859&st=1820#entry128449684",
                            "query_report_unit": "chunk",
                            "relation_edges": [
                                {
                                    "kind": "root_targets_file",
                                    "from_node": "entity:root_action:patch boot.img",
                                    "to_node": "entity:file:boot.img",
                                },
                                {
                                    "kind": "root_uses_tool",
                                    "from_node": "entity:root_action:patch boot.img",
                                    "to_node": "entity:tool:Magisk",
                                },
                            ],
                        },
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = run_live_graph_query_eval_suite(
        run_id,
        suite_path,
        REPO_ROOT,
        artifact_root,
    )

    assert report["schema"] == "aoa_4pda_live_graph_query_eval_report_v1"
    assert report["suite_id"] == "unit-live-graph-query-quality"
    assert report["status"] == "ok"
    assert report["run_id"] == run_id
    assert report["network_touched"] is False
    assert report["source_run_network_touched"] is True
    assert report["artifact_lifecycle"] == "read_existing_configured_storage"
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["checks"]["policy_preserved"] is True
    assert report["checks"]["profile_matches"] is True
    assert report["checks"]["graph_has_relation_edges"] is True
    assert report["counts"]["cases"] == 2
    assert report["counts"]["failed"] == 0

    recovery_case = report["cases"][0]
    assert recovery_case["checks"]["top_post_id"] is True
    assert recovery_case["checks"]["expected_relation_edges_present"] is True
    assert recovery_case["checks"]["graph_report_rerank_intents_all"] is True
    assert recovery_case["checks"]["source_refs_preserved"] is True
    root_case = report["cases"][1]
    assert root_case["checks"]["top_post_id"] is True
    assert root_case["checks"]["graph_report_relation_edge_kinds_all"] is True
    assert root_case["checks"]["graph_report_rerank_intents_all"] is True


def test_live_answer_eval_suite_checks_named_run_without_network(tmp_path):
    run_id = "live-answer-eval-test"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = tmp_path / "data" / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    _write_live_graph_query_eval_topics(normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "cache" / "indexes" / run_id, "xiaomi-13t")
    graph_path = build_graph(normalized_dir, artifact_root / "graphs" / run_id, "xiaomi-13t")
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    _write_receipt(
        receipts_dir,
        run_id,
        "crawl",
        {
            "schema": "aoa_4pda_crawl_receipt_v1",
            "run_id": run_id,
            "profile_id": "xiaomi-13t",
            "policy": {
                "allowed_public_only": True,
                "internal_search_used": False,
                "attachments_downloaded": False,
            },
            "counts": {
                "requested_topics": 1,
                "requested_pages": 1,
                "fetched_topics": 1,
                "fetched_pages": 1,
                "errors": 0,
            },
            "network_touched": True,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "normalize",
        {
            "schema": "aoa_4pda_normalize_receipt_v1",
            "run_id": run_id,
            "source_run_id": run_id,
            "counts": {"topics": 1, "pages": 1},
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "index",
        {
            "schema": "aoa_4pda_index_manifest_v1",
            "index_id": run_id,
            "profile_id": "xiaomi-13t",
            "source_run_ids": [run_id],
            "index_kinds": ["keyword"],
            "index_path": str(index_path),
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "graph",
        {
            "schema": "aoa_4pda_graph_receipt_v1",
            "run_id": run_id,
            "profile_id": "xiaomi-13t",
            "graph_path": str(graph_path),
            "network_touched": False,
        },
    )
    suite_path = tmp_path / "live_answer_suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "schema": "aoa_4pda_live_answer_eval_suite_v1",
                "suite_id": "unit-live-answer-quality",
                "owner_repo": "aoa-4pda-connector",
                "proof_owner_repo": "aoa-evals",
                "central_boundary": "local unit suite only",
                "default_limit": 5,
                "dataset": {
                    "kind": "bounded_live_run_keyword_index_plus_graph_answer",
                    "expected_profile": "xiaomi-13t",
                },
                "cases": [
                    {
                        "case_id": "recovery-answer",
                        "query": "Xiaomi 13T aristotle recovery.img fastboot",
                        "expect": {
                            "top_post_id": "128964413",
                            "answer_kind": "recovery",
                            "source_url_contains": "showtopic=1076859&st=2140#entry128964413",
                            "query_report_unit": "chunk",
                            "matched_specific_terms_all": ["recovery.img"],
                            "query_report_technical_terms_all": ["recovery.img", "aristotle"],
                            "graph_report_relation_edge_kinds_all": [
                                "recovery_targets_file",
                                "recovery_uses_tool",
                            ],
                            "recovery_action_labels": ["flash recovery.img"],
                            "target_file_labels": ["recovery.img"],
                            "tool_labels": ["fastboot"],
                            "answer_context_labels_min": 3,
                        },
                    },
                    {
                        "case_id": "root-answer",
                        "query": "2306EPN60G HyperOS boot.img Magisk KSU",
                        "expect": {
                            "top_post_id": "128449684",
                            "answer_kind": "root",
                            "source_url_contains": "showtopic=1076859&st=1820#entry128449684",
                            "query_report_unit": "chunk",
                            "matched_specific_terms_all": ["boot.img", "magisk"],
                            "query_report_technical_terms_all": ["boot.img"],
                            "graph_report_relation_edge_kinds_all": [
                                "root_targets_file",
                                "root_uses_tool",
                            ],
                            "root_action_labels": ["patch boot.img"],
                            "target_file_labels": ["boot.img"],
                            "tool_labels": ["Magisk"],
                            "answer_context_labels_min": 3,
                        },
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = run_live_answer_eval_suite(
        run_id,
        suite_path,
        REPO_ROOT,
        artifact_root,
    )

    assert report["schema"] == "aoa_4pda_live_answer_eval_report_v1"
    assert report["suite_id"] == "unit-live-answer-quality"
    assert report["status"] == "ok"
    assert report["run_id"] == run_id
    assert report["network_touched"] is False
    assert report["source_run_network_touched"] is True
    assert report["artifact_lifecycle"] == "read_existing_configured_storage"
    assert report["owner_boundary"]["proof_owner_repo"] == "aoa-evals"
    assert report["checks"]["policy_preserved"] is True
    assert report["checks"]["profile_matches"] is True
    assert report["checks"]["graph_has_relation_edges"] is True
    assert report["counts"]["cases"] == 2
    assert report["counts"]["failed"] == 0

    recovery_case = report["cases"][0]
    assert recovery_case["checks"]["answer_kind"] is True
    assert recovery_case["checks"]["expected_labels_present"] is True
    assert recovery_case["checks"]["matched_specific_terms_all"] is True
    assert recovery_case["diagnostics"]["failed_checks"] == []
    assert "recovery.img" in recovery_case["diagnostics"]["top_result_matches"]["matched_specific_terms"]
    assert recovery_case["top_evidence_result"]["post_id"] == "128964413"
    assert recovery_case["top_answer"]["recovery_action_labels"] == ["flash recovery.img"]
    assert recovery_case["checks"]["freshness_present"] is True
    assert recovery_case["checks"]["freshness_note_present"] is True
    assert recovery_case["diagnostics"]["freshness"]["basis"] == "source_post_and_capture_metadata"
    root_case = report["cases"][1]
    assert root_case["checks"]["answer_kind"] is True
    assert root_case["checks"]["answer_context_labels_min"] is True
    assert root_case["diagnostics"]["answer_context"]["label_count"] >= 3
    assert root_case["top_answer"]["root_action_labels"] == ["patch boot.img"]
    assert root_case["checks"]["freshness_present"] is True
    assert root_case["checks"]["freshness_note_present"] is True


def _write_live_search_eval_topics(normalized_dir: Path) -> None:
    topics = [
        {
            "schema": "aoa_4pda_normalized_topic_v1",
            "topic_id": "1019304",
            "page_start": "0",
            "source_url": "https://4pda.to/forum/index.php?showtopic=1019304&st=0",
            "title": "Redmi Note 10 Pro - TWRP and Root",
            "captured_at": "2026-06-19T00:00:00Z",
            "posts": [
                {
                    "schema": "aoa_4pda_normalized_post_v1",
                    "post_id": "105092172",
                    "topic_id": "1019304",
                    "source_url": "https://4pda.to/forum/index.php?showtopic=1019304&st=0#entry105092172",
                    "captured_at": "2026-06-19T00:00:00Z",
                    "author_label": None,
                    "posted_at": None,
                    "text": "Redmi Note 10 Pro root guide. Patch boot.img in Magisk, then use TWRP only when needed.",
                    "entities": [],
                },
                {
                    "schema": "aoa_4pda_normalized_post_v1",
                    "post_id": "105092000",
                    "topic_id": "1019304",
                    "source_url": "https://4pda.to/forum/index.php?showtopic=1019304&st=0#entry105092000",
                    "captured_at": "2026-06-19T00:00:00Z",
                    "author_label": None,
                    "posted_at": None,
                    "text": "Redmi Note 10 Pro discussion. Redmi Note 10 Pro firmware overview and common topic index.",
                    "entities": [],
                },
            ],
        },
        {
            "schema": "aoa_4pda_normalized_topic_v1",
            "topic_id": "1021534",
            "page_start": "0",
            "source_url": "https://4pda.to/forum/index.php?showtopic=1021534&st=0",
            "title": "Redmi Note 10 - Recovery",
            "captured_at": "2026-06-19T00:00:00Z",
            "posts": [
                {
                    "schema": "aoa_4pda_normalized_post_v1",
                    "post_id": "105638716",
                    "topic_id": "1021534",
                    "source_url": "https://4pda.to/forum/index.php?showtopic=1021534&st=0#entry105638716",
                    "captured_at": "2026-06-19T00:00:00Z",
                    "author_label": None,
                    "posted_at": None,
                    "text": (
                        "If bootloop appears, use fastboot flash recovery recovery.img, "
                        "then fastboot boot recovery.img."
                    ),
                    "entities": [],
                },
                {
                    "schema": "aoa_4pda_normalized_post_v1",
                    "post_id": "105638000",
                    "topic_id": "1021534",
                    "source_url": "https://4pda.to/forum/index.php?showtopic=1021534&st=0#entry105638000",
                    "captured_at": "2026-06-19T00:00:00Z",
                    "author_label": None,
                    "posted_at": None,
                    "text": "Redmi Note 10 Redmi Note 10 firmware news and topic navigation.",
                    "entities": [],
                },
            ],
        },
    ]
    for topic in topics:
        (normalized_dir / f"topic-{topic['topic_id']}-st0.json").write_text(
            json.dumps(topic, ensure_ascii=False), encoding="utf-8"
        )


def _write_live_graph_query_eval_topics(normalized_dir: Path) -> None:
    posts = [
        {
            "post_id": "128964413",
            "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry128964413",
            "text": (
                "Xiaomi 13T aristotle на HyperOS. Сама TWRP: "
                "twrp-3.7.1_A13-5.10.136-vendor_boot-aristotle.img. "
                "Родной recovery от стоковой прошивки: recovery.img. "
                "Прошить recovery.img можно через fastboot."
            ),
        },
        {
            "post_id": "128449684",
            "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=1820#entry128449684",
            "text": (
                "Xiaomi 13T 2306EPN60G HyperOS: чтобы установить Magisk, "
                "нужно пропатчить через boot_installer boot.img."
            ),
        },
    ]
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "1076859",
        "page_start": "2140",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-20T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": post["post_id"],
                "topic_id": "1076859",
                "source_url": post["source_url"],
                "captured_at": "2026-06-20T00:00:00Z",
                "author_label": None,
                "posted_at": None,
                "text": post["text"],
                "entities": extract_entities(post["text"]),
            }
            for post in posts
        ],
    }
    (normalized_dir / "topic-1076859-st2140.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )


def _write_live_ranking_pressure_topics(normalized_dir: Path) -> None:
    posts = [
        {
            "post_id": "2001",
            "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=0#entry2001",
            "text": (
                "OrangeFox OrangeFox OrangeFox discussion for Xiaomi 13T. "
                "TWRP fastboot recovery notes and general recovery chatter."
            ),
        },
        {
            "post_id": "2002",
            "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=0#entry2002",
            "text": (
                "Xiaomi 13T aristotle recovery guide. Use TWRP and fastboot to "
                "flash recovery.img when a recovery image is needed."
            ),
        },
    ]
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "1076859",
        "page_start": "0",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=0",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-20T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": post["post_id"],
                "topic_id": "1076859",
                "source_url": post["source_url"],
                "captured_at": "2026-06-20T00:00:00Z",
                "author_label": None,
                "posted_at": None,
                "text": post["text"],
                "entities": extract_entities(post["text"]),
            }
            for post in posts
        ],
    }
    (normalized_dir / "topic-1076859-st0.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")
