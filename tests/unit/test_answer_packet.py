from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aoa_4pda_connector.answer import render_answer_packet
from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.query import query_graph_packet


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_FIXTURE_URL = "https://4pda.to/forum/index.php?showtopic=42&st=0"


def test_render_answer_packet_summarizes_graph_context_without_network(tmp_path):
    index_path, graph_path = _build_live_shape_index_and_graph(tmp_path)
    evidence_packet = query_graph_packet(index_path, graph_path, "bootloop recovery.img camellia", limit=1)

    answer_packet = render_answer_packet(evidence_packet)

    assert answer_packet["schema"] == "aoa_4pda_answer_packet_v1"
    assert answer_packet["policy"]["source"] == "local_keyword_index_plus_graph_answer_renderer"
    assert answer_packet["policy"]["internal_search_used"] is False
    assert answer_packet["answer_report"]["renderer"] == "starter_graph_context_v2"
    assert answer_packet["answer_report"]["source_packet_id"] == evidence_packet["packet_id"]
    assert answer_packet["answer_report"]["freshness_context"] == "source_post_and_capture_metadata"

    answer = answer_packet["answers"][0]
    assert answer["answer_kind"] == "issue_fix_warning"
    assert answer["post_id"] == "9001"
    assert answer["source_url"].endswith("#entry9001")
    assert "bootloop" in answer["answer_text"]
    assert "flash recovery.img" in answer["answer_text"]
    assert "restore boot.img" in answer["answer_text"]
    assert "do not install recovery.img from camellia" in answer["answer_text"]
    assert answer["issue_labels"] == ["bootloop"]
    assert answer["fix_labels"] == ["flash recovery.img", "restore boot.img"]
    assert answer["warning_labels"] == ["do not install recovery.img from camellia"]
    assert answer["warned_target_labels"] == ["camellia", "recovery.img"]
    assert answer["recovery_action_labels"] == ["flash recovery.img"]
    assert answer["target_file_labels"] == ["recovery.img"]
    assert answer["tool_labels"] == ["fastboot", "TWRP"]
    assert answer["confidence"]["basis"] == "starter_graph_context"
    assert answer["evidence_refs"] == ["chunk:42:9001:chunk-000", "post:9001"]
    assert answer["posted_at"] == "01.04.21, 09:32"
    assert answer["captured_at"]
    assert answer["freshness"]["basis"] == "source_post_and_capture_metadata"
    assert answer["freshness"]["posted_at"] == answer["posted_at"]
    assert answer["freshness"]["captured_at"] == answer["captured_at"]
    assert answer["freshness"]["packet_created_at"] == answer_packet["created_at"]
    assert "Public post timestamp" in answer["freshness"]["note"]


def test_render_answer_packet_preserves_xiaomi_root_recovery_relation_context(tmp_path):
    index_path, graph_path = _build_xiaomi_13t_index_and_graph(tmp_path)
    evidence_packet = query_graph_packet(
        index_path,
        graph_path,
        "Xiaomi 13T aristotle recovery.img boot.img Magisk KSU fastboot",
        limit=1,
    )

    answer_packet = render_answer_packet(evidence_packet)

    answer = answer_packet["answers"][0]
    assert answer_packet["answer_report"]["renderer"] == "starter_graph_context_v2"
    assert answer["answer_kind"] == "root_recovery"
    assert answer["post_id"] == "128964413"
    assert answer["root_action_labels"] == ["patch boot.img"]
    assert answer["recovery_action_labels"] == ["flash recovery.img"]
    assert answer["target_file_labels"] == ["boot.img", "recovery.img"]
    assert answer["tool_labels"] == ["KSU", "Magisk", "fastboot", "OrangeFox", "TWRP"]
    assert answer["firmware_context_labels"] == ["HyperOS", "HyperOS 2.0.2"]
    assert "Root actions: patch boot.img." in answer["answer_text"]
    assert "Recovery actions: flash recovery.img." in answer["answer_text"]
    assert "Firmware context: HyperOS; HyperOS 2.0.2." in answer["answer_text"]
    assert answer["source_refs"] == [
        "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry128964413"
    ]
    assert answer["posted_at"] == "20.06.26, 12:00"
    assert answer["captured_at"]
    assert answer["freshness"]["basis"] == "source_post_and_capture_metadata"


def test_cli_answer_uses_external_index_and_graph_without_network(tmp_path):
    run_id = "answer-test"
    data_root = tmp_path / "data"
    cache_root = tmp_path / "cache"
    artifact_root = tmp_path / "artifacts"
    normalized_dir = data_root / "normalized" / run_id
    normalized_dir.mkdir(parents=True)
    normalize_snapshot(REPO_ROOT / "connector/fixtures/html/live_shape_topic.html", LIVE_FIXTURE_URL, normalized_dir)
    index_path = build_keyword_index(normalized_dir, cache_root / "indexes" / run_id, "starter")
    graph_path = build_graph(normalized_dir, artifact_root / "graphs" / run_id, "starter")

    receipts_dir = artifact_root / "receipts"
    receipts_dir.mkdir(parents=True)
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

    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(REPO_ROOT / "src"),
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

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["schema"] == "aoa_4pda_answer_packet_v1"
    assert payload["network_touched"] is False
    assert payload["answers"][0]["post_id"] == "9001"
    assert payload["answers"][0]["fix_labels"] == ["flash recovery.img", "restore boot.img"]
    assert payload["answers"][0]["freshness"]["basis"] == "source_post_and_capture_metadata"
    assert payload["answers"][0]["captured_at"]


def _build_live_shape_index_and_graph(tmp_path: Path) -> tuple[Path, Path]:
    normalized_dir = tmp_path / "normalized"
    normalize_snapshot(REPO_ROOT / "connector/fixtures/html/live_shape_topic.html", LIVE_FIXTURE_URL, normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "index", "starter")
    graph_path = build_graph(normalized_dir, tmp_path / "graph", "starter")
    return index_path, graph_path


def _build_xiaomi_13t_index_and_graph(tmp_path: Path) -> tuple[Path, Path]:
    normalized_dir = tmp_path / "normalized-xiaomi"
    normalize_snapshot(
        REPO_ROOT / "connector/fixtures/html/xiaomi_13t_firmware_topic.html",
        "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        normalized_dir,
    )
    index_path = build_keyword_index(normalized_dir, tmp_path / "index-xiaomi", "xiaomi-13t")
    graph_path = build_graph(normalized_dir, tmp_path / "graph-xiaomi", "xiaomi-13t")
    return index_path, graph_path


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")
