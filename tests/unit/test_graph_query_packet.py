from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import extract_entities, normalize_snapshot
from aoa_4pda_connector.query import query_graph_packet, query_hybrid_packet
from aoa_4pda_connector.vector import build_vector_index


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_FIXTURE_URL = "https://4pda.to/forum/index.php?showtopic=42&st=0"


def test_query_graph_packet_attaches_relation_context_without_network(tmp_path):
    index_path, graph_path = _build_live_shape_index_and_graph(tmp_path)

    packet = query_graph_packet(index_path, graph_path, "bootloop recovery.img camellia", limit=1)

    assert packet["schema"] == "aoa_4pda_evidence_packet_v1"
    assert packet["policy"]["source"] == "local_keyword_index_plus_graph"
    assert packet["policy"]["internal_search_used"] is False
    assert packet["graph_report"]["graph_path"] == str(graph_path)
    assert {"fixes_issue", "warns_about"}.issubset(set(packet["graph_report"]["relation_edge_kinds"]))

    result = packet["results"][0]
    assert result["post_id"] == "9001"
    context = result["graph_context"]
    assert context["post_node"] == "post:9001"
    assert "entity:issue:bootloop" in context["entity_node_ids"]

    relation_edges = {
        (edge["kind"], edge["from_node"], edge["to_node"])
        for edge in context["relation_edges"]
    }
    assert (
        "fixes_issue",
        "entity:fix:flash recovery.img",
        "entity:issue:bootloop",
    ) in relation_edges
    assert (
        "warns_about",
        "entity:warning:do not install recovery.img from camellia",
        "entity:file:recovery.img",
    ) in relation_edges
    assert (
        "warns_about",
        "entity:warning:do not install recovery.img from camellia",
        "entity:codename:camellia",
    ) in relation_edges

    fix_context = {
        fix["node_id"]: fix["fixes_issue_node_ids"]
        for fix in context["fixes"]
    }
    assert fix_context["entity:fix:flash recovery.img"] == ["entity:issue:bootloop"]

    warning_context = {
        warning["node_id"]: warning["warns_about_node_ids"]
        for warning in context["warnings"]
    }
    assert warning_context["entity:warning:do not install recovery.img from camellia"] == [
        "entity:codename:camellia",
        "entity:file:recovery.img",
    ]


def test_cli_query_graph_uses_external_index_and_graph_without_network(tmp_path):
    run_id = "graph-query-test"
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
            "query-graph",
            "bootloop recovery.img camellia",
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
    assert payload["network_touched"] is False
    assert payload["results"][0]["post_id"] == "9001"
    edge_kinds = {edge["kind"] for edge in payload["results"][0]["graph_context"]["relation_edges"]}
    assert {"fixes_issue", "warns_about"}.issubset(edge_kinds)


def test_query_graph_packet_carries_xiaomi_root_and_recovery_relations(tmp_path):
    index_path, graph_path = _build_xiaomi_firmware_index_and_graph(tmp_path)

    packet = query_graph_packet(index_path, graph_path, "Xiaomi 13T aristotle recovery.img", limit=1)

    assert {
        "recovery_targets_file",
        "recovery_uses_tool",
        "root_targets_file",
        "root_uses_tool",
    }.issubset(set(packet["graph_report"]["relation_edge_kinds"]))

    result = packet["results"][0]
    assert result["post_id"] == "128964413"
    relation_edges = {
        (edge["kind"], edge["from_node"], edge["to_node"])
        for edge in result["graph_context"]["relation_edges"]
    }

    assert (
        "recovery_targets_file",
        "entity:recovery_action:flash recovery.img",
        "entity:file:recovery.img",
    ) in relation_edges
    assert (
        "recovery_uses_tool",
        "entity:recovery_action:flash recovery.img",
        "entity:tool:fastboot",
    ) in relation_edges
    assert (
        "root_uses_tool",
        "entity:root_action:patch boot.img",
        "entity:tool:Magisk",
    ) in relation_edges


def test_query_graph_packet_relation_reranks_recovery_intent(tmp_path):
    normalized_dir = tmp_path / "normalized-rerank"
    normalized_dir.mkdir()
    noisy_text = (
        "OrangeFox OrangeFox OrangeFox for Xiaomi 13T. "
        "TWRP fastboot recovery notes and general discussion."
    )
    structured_text = (
        "Xiaomi 13T aristotle recovery guide. TWRP build uses vendor_boot. "
        "Прошить recovery.img можно через fastboot."
    )
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "1076859",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-21T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "2001",
                "topic_id": "1076859",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry2001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-21T00:00:00Z",
                "text": noisy_text,
                "entities": extract_entities(noisy_text),
            },
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "2002",
                "topic_id": "1076859",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry2002",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-21T00:00:00Z",
                "text": structured_text,
                "entities": extract_entities(structured_text),
            },
        ],
    }
    (normalized_dir / "topic-1076859-st2140.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )
    index_path = build_keyword_index(normalized_dir, tmp_path / "index-rerank", "xiaomi-13t")
    graph_path = build_graph(normalized_dir, tmp_path / "graph-rerank", "xiaomi-13t")

    packet = query_graph_packet(index_path, graph_path, "OrangeFox TWRP Xiaomi 13T fastboot recovery", limit=2)

    assert packet["graph_report"]["rerank"] == {
        "algorithm": "relation_intent_v1",
        "applied": True,
        "intents": ["recovery"],
    }
    top = packet["results"][0]
    assert top["post_id"] == "2002"
    assert top["keyword_rank"] == 2
    assert top["graph_rank"] == 1
    assert top["relation_rerank"]["matching_edge_count"] >= 2
    assert {
        "recovery_targets_file",
        "recovery_uses_tool",
    }.issubset(set(top["relation_rerank"]["matching_relation_kinds"]))
    assert packet["results"][1]["post_id"] == "2001"
    assert packet["results"][1]["keyword_rank"] == 1


def test_query_hybrid_packet_boosts_matching_graph_relations(tmp_path):
    normalized_dir = tmp_path / "normalized-hybrid-rerank"
    normalized_dir.mkdir()
    noisy_text = (
        "OrangeFox OrangeFox OrangeFox Xiaomi 13T TWRP fastboot recovery. "
        "General index notes without a concrete recovery image flashing relation."
    )
    structured_text = (
        "Xiaomi 13T aristotle recovery guide. TWRP build uses vendor_boot. "
        "Прошить recovery.img можно через fastboot."
    )
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "1076859",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-21T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "3001",
                "topic_id": "1076859",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry3001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-21T00:00:00Z",
                "text": noisy_text,
                "entities": extract_entities(noisy_text),
            },
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "3002",
                "topic_id": "1076859",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry3002",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-21T00:00:00Z",
                "text": structured_text,
                "entities": extract_entities(structured_text),
            },
        ],
    }
    (normalized_dir / "topic-1076859-st2140.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )
    index_path = build_keyword_index(normalized_dir, tmp_path / "index-hybrid-rerank", "xiaomi-13t")
    vector_path = build_vector_index(normalized_dir, tmp_path / "vector-hybrid-rerank", "xiaomi-13t")
    graph_path = build_graph(normalized_dir, tmp_path / "graph-hybrid-rerank", "xiaomi-13t")

    packet = query_hybrid_packet(
        index_path,
        vector_path,
        graph_path,
        "OrangeFox TWRP Xiaomi 13T fastboot recovery",
        limit=2,
    )

    top = packet["results"][0]
    assert packet["query_report"]["algorithm"] == "hybrid_bm25_vector_graph_v1"
    assert packet["hybrid_report"]["algorithm"] == "weighted_normalized_keyword_vector_relation_boost_v1"
    assert packet["hybrid_report"]["graph_relation_boost"]["algorithm"] == "relation_intent_saturation_v1"
    assert top["post_id"] == "3002"
    assert top["keyword_rank"] == 2
    assert top["score_breakdown"]["graph_raw"] > 0
    assert top["score_breakdown"]["graph_relation_boost"] > 0
    assert packet["results"][1]["post_id"] == "3001"


def _build_live_shape_index_and_graph(tmp_path: Path) -> tuple[Path, Path]:
    normalized_dir = tmp_path / "normalized"
    normalize_snapshot(REPO_ROOT / "connector/fixtures/html/live_shape_topic.html", LIVE_FIXTURE_URL, normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "index", "starter")
    graph_path = build_graph(normalized_dir, tmp_path / "graph", "starter")
    return index_path, graph_path


def _build_xiaomi_firmware_index_and_graph(tmp_path: Path) -> tuple[Path, Path]:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    text = (
        "Xiaomi 13T 2306EPN60G aristotle на HyperOS 2.0.2. "
        "Можно пропатчить boot.img через Magisk или KSU. "
        "Сама TWRP: twrp-3.7.1_A13-5.10.136-vendor_boot-aristotle.img. "
        "Родной recovery от стоковой прошивки: recovery.img. "
        "Orange Fox for Xiaomi 13T тоже прошивается через fastboot."
    )
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "1076859",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-20T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "128964413",
                "topic_id": "1076859",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry128964413",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-20T00:00:00Z",
                "text": text,
                "entities": extract_entities(text),
            }
        ],
    }
    (normalized_dir / "topic-1076859-st2140.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )
    index_path = build_keyword_index(normalized_dir, tmp_path / "index", "xiaomi-13t")
    graph_path = build_graph(normalized_dir, tmp_path / "graph", "xiaomi-13t")
    return index_path, graph_path


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")
