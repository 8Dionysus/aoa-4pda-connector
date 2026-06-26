from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.vector import build_vector_index


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
    assert criteria["answer_quality_gates"]["evidence"]["gap_awareness_field_or_note_present"] is True
    assert criteria["answer_quality_gates"]["evidence"]["chain_awareness_field_or_note_present"] is True
    assert criteria["answer_quality_gates"]["evidence"]["synthesis_field_or_note_present"] is True
    assert criteria["reference_profile_seed_review_state"]["status"] == "partial"
    assert criteria["reference_profile_seed_review_state"]["evidence"]["review_status"] == "missing_run"
    assert criteria["reference_profile_coverage_state"]["status"] == "partial"
    assert criteria["reference_profile_coverage_state"]["evidence"]["coverage_status"] == "no_run"
    assert criteria["reference_profile_information_need_coverage"]["status"] == "partial"
    info_evidence = criteria["reference_profile_information_need_coverage"]["evidence"]
    assert info_evidence["matrix_exists"] is True
    assert info_evidence["connector_ready_complete"] is False
    assert info_evidence["deep_profile_complete"] is False
    assert len(info_evidence["deep_profile_missing_need_ids"]) == 15
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
    assert materialized["counts"]["vector_docs"] == 1
    assert materialized["counts"]["graph_edges"] >= 4
    assert (artifact_root / "receipts" / f"{run_id}.index.json").is_file()
    assert (artifact_root / "receipts" / f"{run_id}.vector.json").is_file()
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
    assert packet["answer_report"]["answer_status"] == "answered"
    assert packet["answers"][0]["post_id"] == "9001"
    assert packet["agent_answer"]["status"] == "answered"
    assert packet["agent_answer"]["citations"][0]["post_id"] == "9001"

    no_answer = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "answer",
            "xyznotfound123 no-such-token",
            "--run",
            run_id,
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert no_answer.returncode == 0, no_answer.stdout + no_answer.stderr
    no_answer_packet = json.loads(no_answer.stdout)
    assert no_answer_packet["schema"] == "aoa_4pda_answer_packet_v1"
    assert no_answer_packet["network_touched"] is False
    assert no_answer_packet["answers"] == []
    assert no_answer_packet["answer_report"]["answer_status"] == "insufficient_evidence"
    assert no_answer_packet["answer_report"]["gap_reason"] == "no_candidate_evidence"
    assert "В базе недостаточно данных" in no_answer_packet["answer_report"]["missing_evidence_note"]

    hybrid = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "query-hybrid",
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
    assert hybrid.returncode == 0, hybrid.stdout + hybrid.stderr
    hybrid_packet = json.loads(hybrid.stdout)
    assert hybrid_packet["schema"] == "aoa_4pda_evidence_packet_v1"
    assert hybrid_packet["network_touched"] is False
    assert hybrid_packet["query_report"]["algorithm"] == "hybrid_bm25_vector_graph_v1"
    assert hybrid_packet["results"][0]["post_id"] == "9001"


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
    assert payload["routes"]["information_need_matrix"] == "connector/profiles/xiaomi_13t_information_needs.json"
    assert payload["quality_gates"]["live_ranking_pressure_suite"] == "evals/suites/live_xiaomi_13t_ranking_pressure.json"
    assert payload["quality_gates"]["live_hybrid_query_suite"] == "evals/suites/live_xiaomi_13t_hybrid_query_quality.json"
    assert payload["quality_gates"]["live_graph_query_suite"] == "evals/suites/live_xiaomi_13t_graph_query_quality.json"
    assert payload["quality_gates"]["live_answer_suite"] == "evals/suites/live_xiaomi_13t_answer_quality.json"
    assert payload["limits"]["max_topics"] == 23
    assert payload["seed"]["topic_count"] == 23
    assert "xiaomi-13t-firmware" in payload["seed"]["topic_ids"]
    assert "xiaomi-13t-firmware-boot-recovery-1800" in payload["seed"]["topic_ids"]
    assert "xiaomi-13t-kernelsu-instruction" in payload["seed"]["topic_ids"]
    assert "xiaomi-13t-firmware-window-7140" in payload["seed"]["topic_ids"]
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


def test_cli_coverage_audit_reports_xiaomi_no_run_without_network(tmp_path):
    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(tmp_path / "data"),
            "CONNECTOR_CACHE_ROOT": str(tmp_path / "cache"),
            "CONNECTOR_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "coverage", "audit", "xiaomi-13t"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_coverage_audit_v1"
    assert payload["target_status"] == "reference-profile-coverage-v1"
    assert payload["status"] == "no_run"
    assert payload["profile_id"] == "xiaomi-13t"
    assert payload["seed_plan"]["seed_count"] == 23
    assert payload["seed_plan"]["expected_page_count"] == 70
    assert payload["coverage"]["seed_pages"]["fetched"] == 0
    assert payload["coverage"]["seeds"]["missing"] == 23
    assert payload["information_needs"]["matrix_exists"] is True
    assert payload["information_needs"]["summary"]["total"] == 15
    assert payload["information_needs"]["summary"]["status_counts"]["unmaterialized"] == 15
    assert payload["checks"]["deep_information_needs_covered"] is False
    assert payload["checks"]["receipt_chain_present"] is False
    assert payload["network_touched"] is False

    strict = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "coverage",
            "audit",
            "xiaomi-13t",
            "--strict",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert strict.returncode == 1, strict.stdout + strict.stderr


def test_cli_coverage_audit_reports_partial_xiaomi_seed_coverage(tmp_path):
    run_id = "coverage-audit-partial-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    source_url = "https://4pda.to/forum/index.php?showtopic=1076859&st=2140"
    normalized_path = normalize_snapshot(
        REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html",
        source_url,
        normalized_dir,
    )
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "xiaomi-13t")
    vector_path = build_vector_index(normalized_dir, cache_root / "vectors" / run_id, "xiaomi-13t")
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
            "snapshots": [
                {
                    "seed_id": "xiaomi-13t-firmware-recovery-2140",
                    "label": "Xiaomi 13T - recovery.img window",
                    "page_index": 0,
                    "page_start": 2140,
                    "url": source_url,
                    "path": str(REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html"),
                    "bytes": 1000,
                    "status": 200,
                }
            ],
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
            "normalized": [{"source_url": source_url, "path": str(normalized_path)}],
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
        "vector",
        {
            "schema": "aoa_4pda_vector_manifest_v1",
            "vector_id": run_id,
            "profile_id": "xiaomi-13t",
            "source_run_ids": [run_id],
            "index_kinds": ["vector"],
            "vector_algorithm": "hashed_char_ngram_vector_v1",
            "vector_path": str(vector_path),
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
            "coverage",
            "audit",
            "xiaomi-13t",
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
    assert payload["status"] == "partial"
    assert payload["coverage"]["seed_pages"]["expected"] == 70
    assert payload["coverage"]["seed_pages"]["fetched"] == 1
    assert payload["coverage"]["seed_pages"]["missing"] == 69
    assert payload["coverage"]["focus_areas"]["captured_focus_areas"] == ["recovery_img_restore"]
    assert "xiaomi-13t-firmware-recovery-2140" in payload["materialized"]["fetched_seed_ids"]
    assert payload["materialized"]["index"]["doc_count"] > 0
    assert payload["materialized"]["graph"]["edge_count"] > 0
    assert payload["checks"]["receipt_chain_present"] is True
    assert payload["checks"]["all_expected_seed_pages_fetched"] is False
    assert payload["information_needs"]["summary"]["covered"] == 2
    assert payload["information_needs"]["summary"]["deep_profile_complete"] is False
    recovery_need = {
        item["need_id"]: item
        for item in payload["information_needs"]["needs"]
    }["recovery_fastboot_twrp"]
    assert recovery_need["status"] == "covered"
    assert recovery_need["eval_route_present"] is True
    assert payload["network_touched"] is False


def test_cli_refresh_audit_reports_missing_run_without_network(tmp_path):
    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(tmp_path / "data"),
            "CONNECTOR_CACHE_ROOT": str(tmp_path / "cache"),
            "CONNECTOR_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "refresh", "audit", "xiaomi-13t"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_refresh_audit_v1"
    assert payload["target_status"] == "reference-profile-refresh-v1"
    assert payload["status"] == "missing_run"
    assert payload["strict_ready"] is False
    assert payload["coverage_status"] == "no_run"
    assert payload["checks"]["receipt_chain_present"] is False
    assert payload["network_touched"] is False

    strict = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "refresh",
            "audit",
            "xiaomi-13t",
            "--strict",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert strict.returncode == 1, strict.stdout + strict.stderr


def test_cli_refresh_audit_reports_stale_xiaomi_run_without_network(tmp_path):
    run_id = "refresh-audit-stale-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    source_url = "https://4pda.to/forum/index.php?showtopic=1076859&st=2140"
    normalized_path = normalize_snapshot(
        REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html",
        source_url,
        normalized_dir,
    )
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "xiaomi-13t")
    vector_path = build_vector_index(normalized_dir, cache_root / "vectors" / run_id, "xiaomi-13t")
    graph_path = build_graph(normalized_dir, artifact_root / "graphs" / run_id, "xiaomi-13t")
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    old_ts = "2000-01-01T00:00:00Z"
    newer_ts = "2000-01-01T00:10:00Z"
    _write_receipt(
        receipts_dir,
        run_id,
        "crawl",
        {
            "schema": "aoa_4pda_crawl_receipt_v1",
            "run_id": run_id,
            "profile_id": "xiaomi-13t",
            "started_at": "20000101T000000Z",
            "finished_at": old_ts,
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
            "snapshots": [
                {
                    "seed_id": "xiaomi-13t-firmware-recovery-2140",
                    "label": "Xiaomi 13T - recovery.img window",
                    "page_index": 0,
                    "page_start": 2140,
                    "url": source_url,
                    "path": str(REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html"),
                    "bytes": 1000,
                    "status": 200,
                }
            ],
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
            "finished_at": newer_ts,
            "normalized": [{"source_url": source_url, "path": str(normalized_path)}],
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
            "built_at": newer_ts,
            "source_run_ids": [run_id],
            "index_kinds": ["keyword"],
            "index_path": str(index_path),
            "network_touched": False,
        },
    )
    _write_receipt(
        receipts_dir,
        run_id,
        "vector",
        {
            "schema": "aoa_4pda_vector_manifest_v1",
            "vector_id": run_id,
            "profile_id": "xiaomi-13t",
            "built_at": newer_ts,
            "source_run_ids": [run_id],
            "index_kinds": ["vector"],
            "vector_algorithm": "hashed_char_ngram_vector_v1",
            "vector_path": str(vector_path),
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
            "built_at": newer_ts,
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
            "refresh",
            "audit",
            "xiaomi-13t",
            "--run",
            run_id,
            "--max-age-hours",
            "24",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "needs_refresh"
    assert payload["strict_ready"] is False
    assert payload["coverage_status"] == "partial"
    assert payload["checks"]["receipt_chain_present"] is True
    assert payload["checks"]["crawl_age_within_limit"] is False
    assert payload["checks"]["derived_not_older_than_crawl"] is True
    assert payload["refresh_plan"]["operator_confirmation_required_for_crawl"] is True
    assert payload["network_touched"] is False
    assert datetime.fromisoformat(payload["now"].replace("Z", "+00:00")).tzinfo == UTC

    strict = subprocess.run(
        [
            sys.executable,
            "-m",
            "aoa_4pda_connector.cli",
            "refresh",
            "audit",
            "xiaomi-13t",
            "--run",
            run_id,
            "--max-age-hours",
            "24",
            "--strict",
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert strict.returncode == 1, strict.stdout + strict.stderr


def test_cli_discovery_audit_reports_missing_run_without_network(tmp_path):
    env = _env_with_src()
    env.update(
        {
            "CONNECTOR_DATA_ROOT": str(tmp_path / "data"),
            "CONNECTOR_CACHE_ROOT": str(tmp_path / "cache"),
            "CONNECTOR_ARTIFACT_ROOT": str(tmp_path / "artifacts"),
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "discovery", "audit", "xiaomi-13t"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_discovery_audit_v1"
    assert payload["target_status"] == "reference-profile-discovery-v1"
    assert payload["status"] == "missing_run"
    assert payload["source_run"]["snapshot_count"] == 0
    assert payload["checks"]["crawl_receipt_present"] is False
    assert payload["network_touched"] is False


def test_cli_discovery_audit_reports_public_topic_candidates_without_network(tmp_path):
    run_id = "discovery-audit-candidates-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    raw_dir = data_root / "raw" / run_id
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "topic-1076859-st2140-test.html"
    raw_path.write_text(
        """
        <html><body>
          <h1>Xiaomi 13T firmware source page</h1>
          <a href="/forum/index.php?showtopic=999999&st=0">Xiaomi 13T related public topic</a>
          <a href="https://4pda.to/forum/index.php?showtopic=1076859&st=2160">covered seed-plan window</a>
          <a href="https://4pda.to/forum/index.php?showtopic=1076859&st=2260">boot.img known topic new window</a>
          <a href="https://4pda.to/forum/index.php?act=search&q=xiaomi">internal search</a>
        </body></html>
        """,
        encoding="utf-8",
    )
    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
    source_url = "https://4pda.to/forum/index.php?showtopic=1076859&st=2140"
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
            "snapshots": [
                {
                    "seed_id": "xiaomi-13t-firmware-recovery-2140",
                    "label": "Xiaomi 13T - recovery.img window",
                    "page_index": 0,
                    "page_start": 2140,
                    "url": source_url,
                    "path": str(raw_path),
                    "bytes": raw_path.stat().st_size,
                    "status": 200,
                }
            ],
            "network_touched": True,
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
            "discovery",
            "audit",
            "xiaomi-13t",
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
    assert payload["status"] == "needs_seed_review"
    assert payload["source_run"]["inspected_snapshot_count"] == 1
    assert payload["discovery"]["candidate_count"] == 2
    assert payload["discovery"]["unseeded_topic_count"] == 1
    assert payload["discovery"]["seed_topic_new_window_count"] == 1
    assert payload["discovery"]["covered_seed_window_link_count"] == 1
    assert payload["discovery"]["denied_link_count"] == 1
    candidate_kinds = {item["candidate_kind"] for item in payload["discovery"]["candidates"]}
    assert candidate_kinds == {"unseeded_topic", "seed_topic_new_window"}
    assert all(item["url"].startswith("https://4pda.to/forum/index.php?showtopic=") for item in payload["discovery"]["candidates"])
    assert all(item["review_priority"] in {"high", "medium", "low"} for item in payload["discovery"]["candidates"])
    assert any("Xiaomi 13T" in " ".join(item["anchor_texts"]) for item in payload["discovery"]["candidates"])
    assert all(item["evidence_contexts"] for item in payload["discovery"]["candidates"])
    assert not any(item["page_start"] == 2160 for item in payload["discovery"]["candidates"])
    assert payload["checks"]["public_candidates_allowed"] is True
    assert payload["checks"]["covered_seed_windows_excluded_from_candidates"] is True
    assert payload["network_touched"] is False


def test_cli_discovery_review_reports_manifest_decisions_without_network(tmp_path):
    run_id = "discovery-review-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    raw_dir = data_root / "raw" / run_id
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "topic-1076859-st2140-test.html"
    raw_path.write_text(
        """
        <html><body>
          <h1>Xiaomi 13T firmware source page</h1>
          <a href="/forum/index.php?showtopic=999999&st=0">generic public topic</a>
          <a href="https://4pda.to/forum/index.php?showtopic=1076859&st=2260">boot.img known topic new window</a>
        </body></html>
        """,
        encoding="utf-8",
    )
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
            "snapshots": [
                {
                    "seed_id": "xiaomi-13t-firmware-recovery-2140",
                    "label": "Xiaomi 13T - recovery.img window",
                    "page_index": 0,
                    "page_start": 2140,
                    "url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
                    "path": str(raw_path),
                    "bytes": raw_path.stat().st_size,
                    "status": 200,
                }
            ],
            "network_touched": True,
        },
    )
    manifest_path = tmp_path / "review.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "aoa_4pda_discovery_review_manifest_v1",
                "profile_id": "xiaomi-13t",
                "reviewed_at": "2026-06-21",
                "source_discovery_run": run_id,
                "rules": [
                    {
                        "id": "known-topic-windows",
                        "candidate_kind": "seed_topic_new_window",
                        "decision": "accept",
                        "rationale": "accept known topic windows for bounded seed expansion",
                    }
                ],
                "decisions": [
                    {
                        "url": "https://4pda.to/forum/index.php?showtopic=999999&st=0",
                        "decision": "reject",
                        "rationale": "generic topic is outside this test seed scope",
                    }
                ],
            }
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
            "discovery",
            "review",
            "xiaomi-13t",
            "--run",
            run_id,
            "--manifest",
            str(manifest_path),
        ],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_discovery_review_audit_v1"
    assert payload["target_status"] == "reference-profile-seed-review-v1"
    assert payload["status"] == "reviewed_pending_seed_update"
    assert payload["discovery"]["candidate_count"] == 2
    assert payload["discovery"]["unreviewed_count"] == 0
    assert payload["discovery"]["accepted_missing_from_seed_count"] == 1
    assert payload["discovery"]["decision_counts"]["accept"] == 1
    assert payload["discovery"]["decision_counts"]["reject"] == 1
    assert payload["accepted_missing_from_seed"][0]["candidate_kind"] == "seed_topic_new_window"
    assert payload["checks"]["all_current_candidates_reviewed"] is True
    assert payload["checks"]["accepted_candidates_seeded"] is False
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


def test_cli_live_hybrid_query_eval_reads_configured_storage_without_network(tmp_path):
    run_id = "cli-live-hybrid-query-eval-test"
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
    vector_path = build_vector_index(normalized_dir, cache_root / "vectors" / run_id, "xiaomi-13t")
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
        "vector",
        {
            "schema": "aoa_4pda_vector_manifest_v1",
            "vector_id": run_id,
            "profile_id": "xiaomi-13t",
            "source_run_ids": [run_id],
            "index_kinds": ["vector"],
            "vector_algorithm": "hashed_char_ngram_vector_v1",
            "vector_path": str(vector_path),
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
    suite_path = tmp_path / "live_hybrid_query_suite.json"
    suite_path.write_text(
        json.dumps(
            {
                "schema": "aoa_4pda_live_hybrid_query_eval_suite_v1",
                "suite_id": "cli-live-hybrid-query-suite",
                "owner_repo": "aoa-4pda-connector",
                "proof_owner_repo": "aoa-evals",
                "central_boundary": "local test suite only",
                "default_limit": 3,
                "dataset": {
                    "kind": "bounded_live_run_keyword_vector_graph",
                    "expected_profile": "xiaomi-13t",
                },
                "cases": [
                    {
                        "case_id": "hybrid-root-recovery-context",
                        "query": "Xiaomi 13T aristotle recovery.img boot.img Magisk KSU fastboot",
                        "expect": {
                            "top_post_id": "128964413",
                            "top_keyword_score_present": True,
                            "top_vector_score_present": True,
                            "top_graph_score_present": True,
                            "top_graph_context_present": True,
                            "matched_specific_terms_all": ["boot.img", "recovery.img", "magisk"],
                            "source_url_contains": "showtopic=1076859&st=2140#entry128964413",
                            "query_report_algorithm": "hybrid_bm25_vector_graph_v1",
                            "query_report_unit": "chunk",
                            "hybrid_report_algorithm": "weighted_normalized_keyword_vector_relation_boost_v1",
                            "vector_report_algorithm": "hashed_char_ngram_vector_v1",
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
            "live-hybrid-query-quality",
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
    assert payload["schema"] == "aoa_4pda_live_hybrid_query_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "cli-live-hybrid-query-suite"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0
    assert payload["vector"]["algorithm"] == "hashed_char_ngram_vector_v1"


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


def test_cli_hybrid_query_eval_runs_public_safe_suite():
    result = subprocess.run(
        [sys.executable, "-m", "aoa_4pda_connector.cli", "eval", "hybrid-query-packets"],
        cwd=REPO_ROOT,
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_hybrid_query_eval_report_v1"
    assert payload["status"] == "ok"
    assert payload["suite_id"] == "starter-hybrid-query-packets"
    assert payload["network_touched"] is False
    assert payload["counts"]["failed"] == 0
    assert payload["vector"]["algorithm"] == "hashed_char_ngram_vector_v1"


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
