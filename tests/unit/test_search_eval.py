from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.evaluation import (
    run_answer_eval_suite,
    run_graph_eval_suite,
    run_graph_query_eval_suite,
    run_live_search_eval_suite,
    run_search_eval_suite,
)
from aoa_4pda_connector.index import build_keyword_index


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
    assert report["counts"]["cases"] == 2
    assert report["counts"]["failed"] == 0
    assert report["checks"]["policy_preserved"] is True
    assert report["checks"]["index_has_posts"] is True

    boot_case = report["cases"][0]
    assert boot_case["case_id"] == "redmi-note-10-pro-boot-image"
    assert boot_case["checks"]["top_post_id"] is True
    assert boot_case["checks"]["matched_specific_terms_any"] is True
    assert boot_case["checks"]["query_report_specific_terms_all"] is True


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


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")
