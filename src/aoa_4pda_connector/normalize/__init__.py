"""Normalize raw public topic snapshots into JSON records."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.fetch import topic_id_from_url
from aoa_4pda_connector.parse import decode_html, extract_posts, extract_title


def normalize_snapshot(raw_path: Path, source_url: str, output_dir: Path) -> Path:
    document = decode_html(raw_path.read_bytes())
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    topic_id = topic_id_from_url(source_url)
    posts = []
    for post in extract_posts(document):
        post_id = post["post_id"]
        posts.append(
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": post_id,
                "topic_id": topic_id,
                "source_url": f"{source_url}#entry{post_id}",
                "author_label": None,
                "posted_at": None,
                "captured_at": captured_at,
                "text": post["text"],
                "entities": extract_entities(post["text"]),
            }
        )
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": topic_id,
        "source_url": source_url,
        "title": extract_title(document),
        "captured_at": captured_at,
        "posts": posts,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"topic-{topic_id}.json"
    output_path.write_text(json.dumps(topic, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def extract_entities(text: str) -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    lowered = text.lower()
    for token in ["twrp", "magisk", "boot.img", "firmware", "miui", "bootloop", "recovery"]:
        if token in lowered:
            kind = "issue" if token == "bootloop" else "term"
            entities.append({"kind": kind, "value": token})
    return entities
