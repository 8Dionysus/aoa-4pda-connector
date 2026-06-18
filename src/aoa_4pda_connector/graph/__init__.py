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
            nodes[post_node] = {
                "schema": "aoa_4pda_graph_node_v1",
                "node_id": post_node,
                "kind": "post",
                "label": f"Post {post['post_id']}",
                "source_refs": [post.get("source_url")],
                "confidence": 1.0,
            }
            edges.append(
                {
                    "schema": "aoa_4pda_graph_edge_v1",
                    "edge_id": f"{topic_node}->{post_node}",
                    "kind": "topic_contains_post",
                    "from_node": topic_node,
                    "to_node": post_node,
                    "source_refs": [post.get("source_url")],
                    "confidence": 1.0,
                }
            )
            for entity in post.get("entities", []):
                value = entity["value"]
                kind = entity.get("kind", "term")
                entity_node = f"entity:{kind}:{value}"
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
                if post.get("source_url") not in nodes[entity_node]["source_refs"]:
                    nodes[entity_node]["source_refs"].append(post.get("source_url"))
                edges.append(
                    {
                        "schema": "aoa_4pda_graph_edge_v1",
                        "edge_id": f"{post_node}->{entity_node}",
                        "kind": "post_mentions_entity",
                        "from_node": post_node,
                        "to_node": entity_node,
                        "source_refs": [post.get("source_url")],
                        "confidence": 0.6,
                    }
                )
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
