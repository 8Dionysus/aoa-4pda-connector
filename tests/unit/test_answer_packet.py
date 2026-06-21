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


def test_render_answer_packet_reports_insufficient_evidence_for_weak_candidates():
    evidence_packet = {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": "query-weak",
        "query": "совершенно несуществующий вопрос xyznotfound123 Xiaomi 13T",
        "created_at": "2026-06-21T21:40:00Z",
        "query_report": {
            "algorithm": "bm25_exact_v1",
            "terms": [
                "совершенно",
                "несуществующий",
                "вопрос",
                "xyznotfound123",
                "xiaomi",
                "13t",
                "aristotle",
            ],
            "exact_terms": ["xyznotfound123", "13t"],
            "technical_terms": ["aristotle"],
            "specific_terms": ["совершенно", "несуществующий", "вопрос"],
        },
        "results": [
            {
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859#entry1",
                "topic_id": "1076859",
                "post_id": "1",
                "posted_at": "18.03.24, 11:57",
                "captured_at": "2026-06-21T19:57:53Z",
                "chunk_id": "1076859:1:chunk-000",
                "snippet": "Случайное сообщение про Xiaomi 13T и вопрос.",
                "score": 9.5,
                "score_breakdown": {"bm25": 5.25, "exact": 1.75, "phrase": 2.5},
                "matched_terms": ["13t", "aristotle", "xiaomi", "вопрос"],
                "matched_exact_terms": ["13t"],
                "matched_specific_terms": ["вопрос"],
                "matched_phrases": ["xiaomi 13t"],
                "evidence_refs": ["chunk:1076859:1:chunk-000", "post:1"],
                "graph_context": {
                    "source_refs": ["https://4pda.to/forum/index.php?showtopic=1076859#entry1"],
                    "entity_node_ids": [],
                    "relation_edges": [],
                    "issues": [],
                    "fixes": [],
                    "warnings": [],
                    "warned_targets": [],
                },
            }
        ],
        "policy": {"source": "local_keyword_index_plus_graph", "internal_search_used": False},
    }

    answer_packet = render_answer_packet(evidence_packet, limit=1)

    assert answer_packet["answers"] == []
    assert answer_packet["answer_report"]["answer_status"] == "insufficient_evidence"
    assert answer_packet["answer_report"]["gap_reason"] == "unmatched_structured_query_terms"
    assert answer_packet["answer_report"]["candidate_result_count"] == 1
    assert "В базе недостаточно данных" in answer_packet["answer_report"]["missing_evidence_note"]


def test_render_answer_packet_builds_deduped_evidence_chain_with_nuance_report():
    evidence_packet = {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": "query-chain",
        "query": "Xiaomi 13T recovery.img fastboot TWRP",
        "created_at": "2026-06-21T22:10:00Z",
        "query_report": {
            "algorithm": "bm25_exact_v1",
            "terms": ["xiaomi", "13t", "recovery.img", "fastboot", "twrp", "aristotle"],
            "exact_terms": ["13t", "recovery.img"],
            "technical_terms": ["recovery.img", "aristotle"],
            "specific_terms": ["recovery.img", "fastboot", "twrp"],
        },
        "results": [
            _answer_result(
                post_id="128964413",
                chunk_id="1076859:128964413:chunk-000",
                source_url="https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry128964413",
                posted_at="12.03.24, 12:36",
                captured_at="2026-06-21T19:57:53Z",
                snippet="TWRP прошивается через fastboot, recovery.img нужен для Xiaomi 13T.",
                matched_terms=["13t", "aristotle", "fastboot", "recovery.img", "twrp", "xiaomi"],
                matched_exact_terms=["13t", "recovery.img"],
                matched_specific_terms=["fastboot", "recovery.img", "twrp"],
                relation_edges=[
                    {
                        "kind": "recovery_targets_file",
                        "from_node": "entity:recovery_action:flash recovery.img",
                        "to_node": "entity:file:recovery.img",
                        "confidence": 0.5,
                    },
                    {
                        "kind": "recovery_uses_tool",
                        "from_node": "entity:recovery_action:flash recovery.img",
                        "to_node": "entity:tool:fastboot",
                        "confidence": 0.45,
                    },
                ],
                entity_node_ids=[
                    "entity:recovery_action:flash recovery.img",
                    "entity:file:recovery.img",
                    "entity:tool:fastboot",
                    "entity:tool:TWRP",
                ],
            ),
            _answer_result(
                post_id="128964413",
                chunk_id="1076859:128964413:chunk-001",
                source_url="https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry128964413",
                posted_at="12.03.24, 12:36",
                captured_at="2026-06-21T19:57:53Z",
                snippet="Duplicate chunk from the same post with recovery.img and fastboot.",
                matched_terms=["13t", "fastboot", "recovery.img", "xiaomi"],
                matched_exact_terms=["13t", "recovery.img"],
                matched_specific_terms=["fastboot", "recovery.img"],
                relation_edges=[
                    {
                        "kind": "recovery_targets_file",
                        "from_node": "entity:recovery_action:flash recovery.img",
                        "to_node": "entity:file:recovery.img",
                        "confidence": 0.5,
                    }
                ],
                entity_node_ids=["entity:recovery_action:flash recovery.img", "entity:file:recovery.img"],
            ),
            _answer_result(
                post_id="129061756",
                chunk_id="1076859:129061756:chunk-000",
                source_url="https://4pda.to/forum/index.php?showtopic=1076859&st=2160#entry129061756",
                posted_at="16.03.24, 18:26",
                captured_at="2026-06-21T19:57:54Z",
                snippet="Будьте осторожны при использовании TWRP, recovery.img и fastboot.",
                matched_terms=["13t", "fastboot", "recovery.img", "twrp", "xiaomi"],
                matched_exact_terms=["13t", "recovery.img"],
                matched_specific_terms=["fastboot", "recovery.img", "twrp"],
            ),
            _answer_result(
                post_id="143886187",
                chunk_id="1076859:143886187:chunk-000",
                source_url="https://4pda.to/forum/index.php?showtopic=1076859&st=7140#entry143886187",
                posted_at="17.06.26, 08:36",
                captured_at="2026-06-21T19:57:54Z",
                snippet="Случайное сообщение только про Xiaomi 13T.",
                matched_terms=["13t", "aristotle", "xiaomi"],
                matched_exact_terms=["13t"],
                matched_specific_terms=[],
            ),
        ],
        "policy": {"source": "local_keyword_index_plus_graph", "internal_search_used": False},
    }

    answer_packet = render_answer_packet(evidence_packet, limit=4)

    assert answer_packet["answer_report"]["answer_status"] == "answered"
    assert answer_packet["answer_report"]["candidate_result_count"] == 4
    assert answer_packet["answer_report"]["grounded_candidate_count"] == 3
    assert answer_packet["answer_report"]["deduplicated_candidate_count"] == 1
    assert answer_packet["answer_report"]["filtered_candidate_count"] == 1
    assert [answer["post_id"] for answer in answer_packet["answers"]] == ["128964413", "129061756"]

    chain = answer_packet["evidence_chain"]
    assert [step["post_id"] for step in chain] == ["128964413", "129061756"]
    assert chain[0]["role"] == "primary"
    assert chain[0]["relation_kinds"] == ["recovery_targets_file", "recovery_uses_tool"]
    assert chain[0]["matched_content_terms"] == ["fastboot", "recovery.img", "twrp"]
    assert chain[1]["role"] == "related_context"
    assert chain[1]["matched_content_terms"] == ["fastboot", "recovery.img", "twrp"]

    nuance = answer_packet["nuance_report"]
    assert nuance["chain_step_count"] == 2
    assert nuance["post_count"] == 2
    assert nuance["topic_count"] == 1
    assert nuance["relation_kinds"] == ["recovery_targets_file", "recovery_uses_tool"]
    assert nuance["matched_content_terms"] == ["fastboot", "recovery.img", "twrp"]
    assert nuance["freshness"]["latest_captured_at"] == "2026-06-21T19:57:54Z"
    assert nuance["limitations"] == [
        {"kind": "filtered_weak_candidates", "count": 1},
        {"kind": "deduplicated_same_post_chunks", "count": 1},
    ]


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
    assert payload["evidence_chain"][0]["post_id"] == "9001"
    assert payload["nuance_report"]["chain_step_count"] == len(payload["evidence_chain"])


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


def _answer_result(
    *,
    post_id: str,
    chunk_id: str,
    source_url: str,
    posted_at: str,
    captured_at: str,
    snippet: str,
    matched_terms: list[str],
    matched_exact_terms: list[str],
    matched_specific_terms: list[str],
    relation_edges: list[dict[str, object]] | None = None,
    entity_node_ids: list[str] | None = None,
) -> dict[str, object]:
    relation_edges = relation_edges or []
    entity_node_ids = entity_node_ids or []
    return {
        "source_url": source_url,
        "topic_id": "1076859",
        "post_id": post_id,
        "posted_at": posted_at,
        "captured_at": captured_at,
        "chunk_id": chunk_id,
        "snippet": snippet,
        "score": 10.0,
        "score_breakdown": {"bm25": 6.0, "exact": 1.75, "phrase": 2.5},
        "matched_terms": matched_terms,
        "matched_exact_terms": matched_exact_terms,
        "matched_specific_terms": matched_specific_terms,
        "matched_phrases": ["xiaomi 13t"] if "13t" in matched_terms else [],
        "evidence_refs": [f"chunk:{chunk_id}", f"post:{post_id}"],
        "graph_context": {
            "source_refs": [source_url],
            "entity_node_ids": entity_node_ids,
            "relation_edges": relation_edges,
            "issues": [],
            "fixes": [],
            "warnings": [],
            "warned_targets": [],
        },
    }


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")
