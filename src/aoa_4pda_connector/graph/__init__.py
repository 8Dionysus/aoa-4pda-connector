"""Tiny graph builder for starter normalized records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def build_graph(normalized_dir: Path, output_dir: Path, profile_id: str = "starter") -> Path:
    nodes: dict[str, dict[str, object]] = {}
    edges: list[dict[str, object]] = []
    for topic_path in sorted(normalized_dir.glob("topic-*.json")):
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        topic_node = f"topic:{topic['topic_id']}"
        nodes[topic_node] = {
            "schema": "aoa_4pda_graph_node_v1",
            "node_id": topic_node,
            "kind": "topic",
            "label": topic.get("title", topic["topic_id"]),
            "source_refs": [topic.get("source_url")],
            "confidence": 1.0,
        }
        for post in topic.get("posts", []):
            post_node = f"post:{post['post_id']}"
            source_url = post.get("source_url")
            nodes[post_node] = {
                "schema": "aoa_4pda_graph_node_v1",
                "node_id": post_node,
                "kind": "post",
                "label": f"Post {post['post_id']}",
                "source_refs": [source_url],
                "confidence": 1.0,
            }
            edges.append(
                {
                    "schema": "aoa_4pda_graph_edge_v1",
                    "edge_id": f"{topic_node}->{post_node}",
                    "kind": "topic_contains_post",
                    "from_node": topic_node,
                    "to_node": post_node,
                    "source_refs": [source_url],
                    "confidence": 1.0,
                }
            )
            entities = list(post.get("entities", []))
            for entity in entities:
                value = entity["value"]
                kind = entity.get("kind", "term")
                entity_node = _entity_node_id(entity)
                nodes.setdefault(
                    entity_node,
                    {
                        "schema": "aoa_4pda_graph_node_v1",
                        "node_id": entity_node,
                        "kind": kind,
                        "label": value,
                        "source_refs": [],
                        "confidence": 0.6,
                    },
                )
                if source_url not in nodes[entity_node]["source_refs"]:
                    nodes[entity_node]["source_refs"].append(source_url)
                edges.append(
                    {
                        "schema": "aoa_4pda_graph_edge_v1",
                        "edge_id": f"{post_node}->{entity_node}",
                        "kind": "post_mentions_entity",
                        "from_node": post_node,
                        "to_node": entity_node,
                        "source_refs": [source_url],
                        "confidence": 0.6,
                    }
                )
            _append_relation_edges(edges, post_node, entities, source_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "graph.json"
    payload = {
        "schema": "aoa_4pda_graph_export_v1",
        "profile_id": profile_id,
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _append_relation_edges(
    edges: list[dict[str, object]],
    post_node: str,
    entities: list[dict[str, object]],
    source_url: object,
) -> None:
    issues = _entities_by_kind(entities, "issue")
    fixes = _entities_by_kind(entities, "fix")
    warnings = _entities_by_kind(entities, "warning")
    warning_target_kinds = {"file", "codename", "device", "firmware_family", "firmware_version", "build_id"}

    for fix in fixes:
        for issue in issues:
            _append_edge(edges, "fixes_issue", _entity_node_id(fix), _entity_node_id(issue), post_node, source_url, 0.45)

    for warning in warnings:
        warning_text = str(warning.get("value", "")).casefold()
        for target in entities:
            if target.get("kind") not in warning_target_kinds:
                continue
            if str(target.get("value", "")).casefold() not in warning_text:
                continue
            _append_edge(
                edges,
                "warns_about",
                _entity_node_id(warning),
                _entity_node_id(target),
                post_node,
                source_url,
                0.45,
            )


def _append_edge(
    edges: list[dict[str, object]],
    kind: str,
    from_node: str,
    to_node: str,
    post_node: str,
    source_url: object,
    confidence: float,
) -> None:
    edge_id = f"{from_node}->{to_node}:{kind}:{post_node}"
    if any(edge.get("edge_id") == edge_id for edge in edges):
        return
    edges.append(
        {
            "schema": "aoa_4pda_graph_edge_v1",
            "edge_id": edge_id,
            "kind": kind,
            "from_node": from_node,
            "to_node": to_node,
            "source_refs": [source_url],
            "confidence": confidence,
        }
    )


def _entities_by_kind(entities: list[dict[str, object]], kind: str) -> list[dict[str, object]]:
    return [entity for entity in entities if entity.get("kind") == kind]


def _entity_node_id(entity: dict[str, object]) -> str:
    return f"entity:{entity.get('kind', 'term')}:{entity['value']}"
