from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.query import query_graph_packet


REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_FIXTURE_URL = "https://4pda.to/forum/index.php?showtopic=42&st=0"


def test_query_graph_packet_attaches_relation_context_without_network(tmp_path):
    index_path, graph_path = _build_live_shape_index_and_graph(tmp_path)

    packet = query_graph_packet(index_path, graph_path, "bootloop recovery.img camellia", limit=1)

    assert packet["schema"] == "aoa_4pda_evidence_packet_v1"
    assert packet["policy"]["source"] == "local_keyword_index_plus_graph"
    assert packet["policy"]["internal_search_used"] is False
    assert packet["graph_report"]["graph_path"] == str(graph_path)
    assert packet["graph_report"]["relation_edge_kinds"] == ["fixes_issue", "warns_about"]

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


def _build_live_shape_index_and_graph(tmp_path: Path) -> tuple[Path, Path]:
    normalized_dir = tmp_path / "normalized"
    normalize_snapshot(REPO_ROOT / "connector/fixtures/html/live_shape_topic.html", LIVE_FIXTURE_URL, normalized_dir)
    index_path = build_keyword_index(normalized_dir, tmp_path / "index", "starter")
    graph_path = build_graph(normalized_dir, tmp_path / "graph", "starter")
    return index_path, graph_path


def _write_receipt(receipts_dir: Path, run_id: str, kind: str, payload: dict[str, object]) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    (receipts_dir / f"{run_id}.{kind}.json").write_text(encoded, encoding="utf-8")
    (receipts_dir / f"latest_{kind}.json").write_text(encoded, encoding="utf-8")
