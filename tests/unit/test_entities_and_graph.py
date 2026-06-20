from __future__ import annotations

import json

from aoa_4pda_connector.graph import build_graph
from aoa_4pda_connector.normalize import extract_entities


def _entity_pairs(text: str) -> set[tuple[str, str]]:
    return {(entity["kind"], entity["value"]) for entity in extract_entities(text)}


def test_extract_entities_finds_4pda_technical_terms():
    text = (
        "Redmi Note 10 Pro mojito после прошивки MIUI V14.0.7.0 ловит бутлуп. "
        "В TWRP restore boot.img через fastboot, Magisk лучше отключить. "
        "Warning: не ставить recovery.img от camellia."
    )

    pairs = _entity_pairs(text)

    assert ("device", "Redmi Note 10 Pro") in pairs
    assert ("codename", "mojito") in pairs
    assert ("firmware_family", "MIUI") in pairs
    assert ("firmware_version", "V14.0.7.0") in pairs
    assert ("issue", "bootloop") in pairs
    assert ("tool", "TWRP") in pairs
    assert ("tool", "fastboot") in pairs
    assert ("tool", "Magisk") in pairs
    assert ("file", "boot.img") in pairs
    assert ("file", "recovery.img") in pairs
    assert ("fix", "restore boot.img") in pairs
    assert ("warning", "do not install recovery.img from camellia") in pairs


def test_extract_entities_finds_xiaomi_13t_firmware_root_recovery_terms():
    text = (
        "Xiaomi 13T 2306EPN60G aristotle на HyperOS 2.0.2. "
        "Можно пропатчить boot.img через Magisk или KSU. "
        "Сама TWRP: twrp-3.7.1_A13-5.10.136-vendor_boot-aristotle.img. "
        "Родной recovery от стоковой прошивки: recovery.img. "
        "Orange Fox for Xiaomi 13T тоже прошивается через fastboot."
    )

    pairs = _entity_pairs(text)

    assert ("device", "Xiaomi 13T") in pairs
    assert ("device_model", "2306EPN60G") in pairs
    assert ("codename", "aristotle") in pairs
    assert ("firmware_family", "HyperOS") in pairs
    assert ("firmware_version", "HyperOS 2.0.2") in pairs
    assert ("tool", "Magisk") in pairs
    assert ("tool", "KSU") in pairs
    assert ("tool", "TWRP") in pairs
    assert ("tool", "OrangeFox") in pairs
    assert ("tool", "fastboot") in pairs
    assert ("file", "boot.img") in pairs
    assert ("file", "vendor_boot-aristotle.img") in pairs
    assert ("file", "recovery.img") in pairs
    assert ("root_action", "patch boot.img") in pairs
    assert ("recovery_action", "flash recovery.img") in pairs


def test_extract_entities_deduplicates_by_kind_and_value():
    entities = extract_entities("boot.img boot.img Boot.img fastboot Fastboot")
    pairs = [(entity["kind"], entity["value"]) for entity in entities]

    assert pairs.count(("file", "boot.img")) == 1
    assert pairs.count(("tool", "fastboot")) == 1


def test_graph_uses_kind_scoped_entity_nodes(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "entities",
        "source_url": "https://4pda.to/forum/index.php?showtopic=77",
        "title": "Entity Topic",
        "captured_at": "2026-06-18T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "3001",
                "topic_id": "entities",
                "source_url": "https://4pda.to/forum/index.php?showtopic=77#entry3001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "boot.img is both a file mention and a fix target.",
                "entities": [
                    {"kind": "file", "value": "boot.img"},
                    {"kind": "fix", "value": "restore boot.img"},
                ],
            }
        ],
    }
    (normalized_dir / "topic-entities.json").write_text(json.dumps(topic), encoding="utf-8")

    graph_path = build_graph(normalized_dir, tmp_path / "graph")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    node_ids = {node["node_id"] for node in graph["nodes"]}
    edge_targets = {edge["to_node"] for edge in graph["edges"]}

    assert "entity:file:boot.img" in node_ids
    assert "entity:fix:restore boot.img" in node_ids
    assert "entity:file:boot.img" in edge_targets
    assert "entity:fix:restore boot.img" in edge_targets


def test_graph_adds_starter_relation_edges_between_entities(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "relations",
        "source_url": "https://4pda.to/forum/index.php?showtopic=88",
        "title": "Relation Topic",
        "captured_at": "2026-06-19T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "4001",
                "topic_id": "relations",
                "source_url": "https://4pda.to/forum/index.php?showtopic=88#entry4001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-19T00:00:00Z",
                "text": "Restore boot.img for bootloop. Warning: do not install recovery.img from camellia.",
                "entities": [
                    {"kind": "issue", "value": "bootloop"},
                    {"kind": "fix", "value": "restore boot.img"},
                    {"kind": "warning", "value": "do not install recovery.img from camellia"},
                    {"kind": "file", "value": "recovery.img"},
                    {"kind": "file", "value": "boot.img"},
                    {"kind": "codename", "value": "camellia"},
                ],
            }
        ],
    }
    (normalized_dir / "topic-relations.json").write_text(json.dumps(topic), encoding="utf-8")

    graph_path = build_graph(normalized_dir, tmp_path / "graph")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    relation_edges = {
        (edge["kind"], edge["from_node"], edge["to_node"]): edge
        for edge in graph["edges"]
        if edge["kind"] in {"fixes_issue", "warns_about"}
    }

    assert (
        "fixes_issue",
        "entity:fix:restore boot.img",
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
    assert relation_edges[
        ("fixes_issue", "entity:fix:restore boot.img", "entity:issue:bootloop")
    ]["source_refs"] == ["https://4pda.to/forum/index.php?showtopic=88#entry4001"]


def test_graph_adds_xiaomi_root_and_recovery_relation_edges(tmp_path):
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
        "topic_id": "xiaomi-13t-relations",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-20T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "128964413",
                "topic_id": "xiaomi-13t-relations",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859&st=2140#entry128964413",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-20T00:00:00Z",
                "text": text,
                "entities": extract_entities(text),
            }
        ],
    }
    (normalized_dir / "topic-xiaomi-13t-relations.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )

    graph_path = build_graph(normalized_dir, tmp_path / "graph", "xiaomi-13t")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    relation_edges = {
        (edge["kind"], edge["from_node"], edge["to_node"]): edge
        for edge in graph["edges"]
        if edge["kind"] in {"root_targets_file", "root_uses_tool", "recovery_targets_file", "recovery_uses_tool"}
    }

    assert (
        "root_targets_file",
        "entity:root_action:patch boot.img",
        "entity:file:boot.img",
    ) in relation_edges
    assert (
        "root_uses_tool",
        "entity:root_action:patch boot.img",
        "entity:tool:Magisk",
    ) in relation_edges
    assert (
        "root_uses_tool",
        "entity:root_action:patch boot.img",
        "entity:tool:KSU",
    ) in relation_edges
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
