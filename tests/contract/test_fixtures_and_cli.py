from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot


REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_with_src() -> dict[str, str]:
    env = os.environ.copy()
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}:{env['PYTHONPATH']}"
    return env


def _env_with_src_without_storage() -> dict[str, str]:
    env = _env_with_src()
    env.pop("CONNECTOR_DATA_ROOT", None)
    env.pop("CONNECTOR_CACHE_ROOT", None)
    env.pop("CONNECTOR_ARTIFACT_ROOT", None)
    return env


def test_fixture_packet_is_json_and_does_not_use_internal_search():
    packet = json.loads(
        (REPO_ROOT / "connector/fixtures/expected_packets/synthetic_bootloop_packet.json").read_text(
            encoding="utf-8"
        )
    )
    assert packet["schema"] == "aoa_4pda_evidence_packet_v1"
    assert packet["policy"]["internal_search_used"] is False
    assert packet["results"][0]["source_url"].startswith("https://4pda.to/forum/index.php?showtopic=")


def test_cli_doctor_is_safe_without_external_storage():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "doctor"],
        cwd=REPO_ROOT,
        env=_env_with_src_without_storage(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_doctor_v1"
    assert payload["network_touched"] is False
    assert payload["storage_mode"] == "repo_local_default"
    assert payload["storage_roots"]["CONNECTOR_DATA_ROOT"] == str(REPO_ROOT / ".connector-state" / "data")
    assert payload["storage_roots"]["CONNECTOR_CACHE_ROOT"] == str(REPO_ROOT / ".connector-state" / "cache")
    assert payload["storage_roots"]["CONNECTOR_ARTIFACT_ROOT"] == str(
        REPO_ROOT / ".connector-state" / "artifacts"
    )


def test_cli_init_apply_uses_repo_local_state_when_env_is_unset():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "init", "--apply"],
        cwd=REPO_ROOT,
        env=_env_with_src_without_storage(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_init_v1"
    assert payload["status"] == "ok"
    assert payload["storage_mode"] == "repo_local_default"
    assert payload["network_touched"] is False
    assert str(REPO_ROOT / ".connector-state" / "data") in payload["created"]


def test_cli_storage_status_reports_repo_local_default_without_network():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "storage", "status", "--measure"],
        cwd=REPO_ROOT,
        env=_env_with_src_without_storage(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_storage_status_v1"
    assert payload["storage_mode"] == "repo_local_default"
    assert payload["network_touched"] is False
    assert payload["roots"]["data"]["inside_repo_local_state"] is True
    assert payload["roots"]["cache"]["inside_repo_local_state"] is True
    assert payload["roots"]["artifact"]["inside_repo_local_state"] is True
    assert payload["measure"] is True


def test_cli_ready_reports_connector_ready_audit_without_network(tmp_path):
    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(tmp_path / "data"),
            "CONNECTOR_CACHE_ROOT": str(tmp_path / "cache"),
            "CONNECTOR_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "ready"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_connector_ready_audit_v1"
    assert payload["target_status"] == "connector-ready-v1"
    assert payload["status"] == "not_ready"
    assert payload["network_touched"] is False
    assert payload["ready"] is False
    criteria = {item["id"]: item for item in payload["criteria"]}
    assert criteria["fresh_clone_install_route"]["status"] == "achieved"
    assert criteria["runtime_api_contract"]["status"] == "achieved"
    assert criteria["answer_quality_gates"]["status"] == "achieved"
    assert criteria["answer_quality_gates"]["evidence"]["answer_contract_mentions_freshness"] is True
    assert criteria["answer_quality_gates"]["evidence"]["freshness_field_or_note_present"] is True
    assert criteria["next_representative_profile_prepared"]["status"] == "achieved"
    assert "redmi-note-10-pro" in criteria["next_representative_profile_prepared"]["evidence"]["prepared_profiles"]

    strict = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "ready", "--strict"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert strict.returncode == 1, strict.stdout + strict.stderr


def test_cli_materialize_fixture_writes_queryable_local_state_without_network(tmp_path):
    run_id = "materialize-fixture-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(data_root),
            "CONNECTOR_CACHE_ROOT": str(cache_root),
            "CONNECTOR_ARTIFACT_ROOT": str(artifact_root),
        }
    )
    materialize = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "materialize",
            "fixture",
            "--run",
            run_id,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert materialize.returncode == 0, materialize.stdout + materialize.stderr
    materialized = json.loads(materialize.stdout)
    assert materialized["schema"] == "aoa_4pda_materialize_receipt_v1"
    assert materialized["run_id"] == run_id
    assert materialized["network_touched"] is False
    assert materialized["counts"]["index_docs"] == 1
    assert materialized["counts"]["graph_edges"] >= 4
    assert (artifact_root / "receipts" / f"{run_id}.index.json").is_file()
    assert (artifact_root / "receipts" / f"{run_id}.graph.json").is_file()

    answer = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "answer",
            "bootloop recovery.img camellia",
            "--run",
            run_id,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert answer.returncode == 0, answer.stdout + answer.stderr
    packet = json.loads(answer.stdout)
    assert packet["schema"] == "aoa_4pda_answer_packet_v1"
    assert packet["network_touched"] is False
    assert packet["answers"][0]["post_id"] == "9001"


def test_cli_policy_check_denies_service_routes():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "policy", "check"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["internal_search_allowed"] is False
    assert payload["attachments_allowed"] is False


def test_cli_profile_inspect_reports_xiaomi_13t_route_without_network():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "profile", "inspect", "xiaomi-13t"],
        cwd=REPO_ROOT,
        env=_env_with_src_without_storage(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_profile_inspect_v1"
    assert payload["status"] == "ok"
    assert payload["profile_id"] == "xiaomi-13t"
    assert payload["profile_kind"] == "focused-device"
    assert payload["target"]["device_id"] == "xiaomi-13t"
    assert payload["target"]["codename"] == "aristotle"
    assert "2306EPN60G" in payload["target"]["model_aliases"]
    assert payload["routes"]["seed_file"] == "connector/seeds/xiaomi_13t_topics.yaml"
    assert payload["quality_gates"]["live_graph_query_suite"] == "evals/suites/live_xiaomi_13t_graph_query_quality.json"
    assert payload["quality_gates"]["live_answer_suite"] == "evals/suites/live_xiaomi_13t_answer_quality.json"
    assert payload["seed"]["topic_count"] == 9
    assert "xiaomi-13t-firmware" in payload["seed"]["topic_ids"]
    assert "xiaomi-13t-firmware-boot-recovery-1800" in payload["seed"]["topic_ids"]
    assert payload["checks"]["seed_urls_allowed_public_topics"] is True
    assert payload["network_touched"] is False


def test_cli_profile_inspect_reports_redmi_note_10_pro_route_without_network():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "profile", "inspect", "redmi-note-10-pro"],
        cwd=REPO_ROOT,
        env=_env_with_src_without_storage(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_profile_inspect_v1"
    assert payload["status"] == "ok"
    assert payload["profile_id"] == "redmi-note-10-pro"
    assert payload["profile_kind"] == "focused-device"
    assert payload["target"]["device_id"] == "redmi-note-10-pro"
    assert payload["target"]["codename"] == "sweet"
    assert "sweetin" in payload["target"]["model_aliases"]
    assert payload["routes"]["seed_file"] == "connector/seeds/redmi_note_10_pro_topics.yaml"
    assert payload["quality_gates"]["live_search_suite"] == "evals/suites/live_redmi_note_10_pro_search_quality.json"
    assert payload["seed"]["topic_count"] == 4
    assert "redmi-note-10-pro-miui-root-window-0" in payload["seed"]["topic_ids"]
    assert "redmi-note-10-pro-unofficial-recovery-window-0" in payload["seed"]["topic_ids"]
    assert payload["checks"]["seed_urls_allowed_public_topics"] is True
    assert payload["network_touched"] is False


def test_cli_starter_proof_is_offline_and_queryable():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "proof", "starter"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_starter_proof_v1"
    assert payload["status"] == "ok"
    assert payload["network_touched"] is False
    assert payload["external_storage_required"] is False
    assert payload["checks"]["internal_search_unused"] is True
    assert payload["top_result"]["post_id"] == "1002"


def test_cli_search_eval_runs_public_safe_suite():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "eval", "search-quality"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_search_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "starter-search-quality"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0


def test_cli_graph_eval_runs_public_safe_suite():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "eval", "graph-relations"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_graph_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "starter-graph-relations"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0


def test_cli_xiaomi_graph_eval_runs_public_safe_suite():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "eval",
            "graph-relations",
            "--suite",
            "evals/suites/xiaomi_13t_graph_relations.json",
        ],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_graph_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "xiaomi-13t-graph-relations"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0


def test_cli_live_graph_query_eval_reads_configured_storage_without_network(tmp_path):
    run_id = "cli-live-graph-query-eval-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    normalize_snapshot(
        REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html",
        "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        normalized_dir,
    )
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "xiaomi-13t")
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
                "suite_id": "cli-live-graph-query-suite",
                "owner_repo": "aoa-4pda-connector",
                "proof_owner_repo": "aoa-evals",
                "central_boundary": "local test suite only",
                "default_limit": 3,
                "dataset": {
                    "kind": "bounded_live_run_keyword_index_plus_graph",
                    "expected_profile": "xiaomi-13t",
                },
                "cases": [
                    {
                        "case_id": "recovery-context",
                        "query": "Xiaomi 13T aristotle recovery.img fastboot",
                        "expect": {
                            "top_post_id": "128964413",
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
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(data_root),
            "CONNECTOR_CACHE_ROOT": str(cache_root),
            "CONNECTOR_ARTIFACT_ROOT": str(artifact_root),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "eval",
            "live-graph-query-quality",
            "--run",
            run_id,
            "--suite",
            str(suite_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_live_graph_query_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "cli-live-graph-query-suite"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0


def test_cli_live_answer_eval_reads_configured_storage_without_network(tmp_path):
    run_id = "cli-live-answer-eval-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    normalize_snapshot(
        REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html",
        "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        normalized_dir,
    )
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "xiaomi-13t")
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
                "suite_id": "cli-live-answer-suite",
                "owner_repo": "aoa-4pda-connector",
                "proof_owner_repo": "aoa-evals",
                "central_boundary": "local test suite only",
                "default_limit": 3,
                "dataset": {
                    "kind": "bounded_live_run_keyword_index_plus_graph_answer",
                    "expected_profile": "xiaomi-13t",
                },
                "cases": [
                    {
                        "case_id": "root-recovery-answer",
                        "query": "Xiaomi 13T aristotle recovery.img boot.img Magisk KSU fastboot",
                        "expect": {
                            "top_post_id": "128964413",
                            "answer_kind": "root_recovery",
                            "source_url_contains": "showtopic=1076859&st=2140#entry128964413",
                            "root_action_labels": ["patch boot.img"],
                            "recovery_action_labels": ["flash recovery.img"],
                            "target_file_labels": ["boot.img", "recovery.img"],
                            "tool_labels": ["Magisk", "KSU", "fastboot"],
                        },
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(data_root),
            "CONNECTOR_CACHE_ROOT": str(cache_root),
            "CONNECTOR_ARTIFACT_ROOT": str(artifact_root),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "eval",
            "live-answer-quality",
            "--run",
            run_id,
            "--suite",
            str(suite_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_live_answer_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "cli-live-answer-suite"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0
    assert payload["cases"][0]["top_answer"]["answer_kind"] == "root_recovery"


def test_cli_graph_query_eval_runs_public_safe_suite():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "eval", "graph-query-packets"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_graph_query_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "starter-graph-query-packets"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0


def test_cli_answer_eval_runs_public_safe_suite():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "eval", "answer-packets"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_answer_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "starter-answer-packets"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0


def test_cli_live_search_eval_checks_named_run_without_network(tmp_path):
    run_id = "live-search-eval-cli-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    _write_live_search_eval_topics(normalized_dir)
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "starter")
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

    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(data_root),
            "CONNECTOR_CACHE_ROOT": str(cache_root),
            "CONNECTOR_ARTIFACT_ROOT": str(artifact_root),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "eval",
            "live-search-quality",
            "--run",
            run_id,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_live_search_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "live-starter-search-quality"
    assert payload["run_id"] == run_id
    assert payload["network_touched"] is False
    assert payload["source_run_network_touched"] is True
    assert payload["counts"]["failed"] == 0
    assert payload["cases"][0]["checks"]["matched_specific_terms_any"] is True


def test_cli_live_starter_proof_checks_named_external_run(tmp_path):
    run_id = "live-proof-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / "connector/fixtures/normalized/synthetic_topic.json",
        normalized_dir / "topic-synthetic-topic-1.json",
    )
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "starter")
    graph_path = build_graph(normalized_dir, artifact_root / "graphs" / run_id, "starter")
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
            "source_urls": ["https://4pda.to/forum/index.php?showtopic=000001&st=0"],
            "policy": {
                "allowed_public_only": True,
                "internal_search_used": False,
                "attachments_downloaded": False,
            },
            "counts": {"requested": 1, "fetched": 1, "errors": 0},
            "snapshots": [],
            "errors": [],
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
            "normalized": [{"source_url": "https://4pda.to/forum/index.php?showtopic=000001&st=0"}],
            "counts": {"topics": 1},
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
            "artifact_root": str(index_path.parent),
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
            "profile_id": "starter",
            "graph_path": str(graph_path),
            "network_touched": False,
        },
    )

    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(data_root),
            "CONNECTOR_CACHE_ROOT": str(cache_root),
            "CONNECTOR_ARTIFACT_ROOT": str(artifact_root),
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "proof",
            "live-starter",
            "--run",
            run_id,
            "--query",
            "bootloop boot.img firmware",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_live_starter_proof_v1"
    assert payload["status"] == "ok"
    assert payload["run_id"] == run_id
    assert payload["proof_command_network_touched"] is False
    assert payload["source_run_network_touched"] is True
    assert payload["checks"]["policy_preserved"] is True
    assert payload["checks"]["query_returns_result"] is True
    assert payload["counts"]["index_docs"] == 2


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")


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
