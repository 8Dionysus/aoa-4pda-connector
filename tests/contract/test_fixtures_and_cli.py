from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index


REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_with_src() -> dict[str, str]:
    env = os.environ.copy()
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src if not env.get("PYTHONPATH") else f"{src}:{env['PYTHONPATH']}"
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
        env=_env_with_src(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "aoa_4pda_doctor_v1"
    assert payload["network_touched"] is False


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
