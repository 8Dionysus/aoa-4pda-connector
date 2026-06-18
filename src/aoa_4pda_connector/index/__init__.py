"""Tiny local keyword index for starter data."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


TOKEN_RE = re.compile(r"[\w.\-]+", re.U)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 1]


def build_keyword_index(normalized_dir: Path, output_dir: Path, profile_id: str = "starter") -> Path:
    docs: list[dict[str, object]] = []
    inverted: dict[str, list[dict[str, object]]] = defaultdict(list)
    for topic_path in sorted(normalized_dir.glob("topic-*.json")):
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        for post in topic.get("posts", []):
            text = str(post.get("text", ""))
            doc_id = f"{post.get('topic_id')}:{post.get('post_id')}"
            counts = Counter(tokenize(text))
            docs.append(
                {
                    "doc_id": doc_id,
                    "topic_id": post.get("topic_id"),
                    "post_id": post.get("post_id"),
                    "source_url": post.get("source_url"),
                    "title": topic.get("title"),
                    "text": text,
                    "tokens": sum(counts.values()),
                }
            )
            for token, count in counts.items():
                inverted[token].append({"doc_id": doc_id, "count": count})
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "keyword_index.json"
    payload = {
        "schema": "aoa_4pda_keyword_index_v1",
        "profile_id": profile_id,
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "doc_count": len(docs),
        "term_count": len(inverted),
        "docs": docs,
        "inverted": inverted,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
