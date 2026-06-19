from __future__ import annotations

from pathlib import Path

from aoa_4pda_connector.evaluation import run_search_eval_suite


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
