"""Tiny local keyword index for starter data."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]+(?:[._/\-][0-9A-Za-zА-Яа-яЁё]+)*", re.U)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text) if len(token) > 1]


def extract_exact_terms(tokens: list[str]) -> list[str]:
    exact_terms: list[str] = []
    for token in tokens:
        if _is_exact_term(token) and token not in exact_terms:
            exact_terms.append(token)
    return exact_terms


def build_keyword_index(normalized_dir: Path, output_dir: Path, profile_id: str = "starter") -> Path:
    docs: list[dict[str, object]] = []
    inverted: dict[str, list[dict[str, object]]] = defaultdict(list)
    exact: dict[str, list[str]] = defaultdict(list)
    for topic_path in sorted(normalized_dir.glob("topic-*.json")):
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        title = str(topic.get("title", ""))
        for post in topic.get("posts", []):
            text = str(post.get("text", ""))
            doc_id = f"{post.get('topic_id')}:{post.get('post_id')}"
            search_text = f"{title} {text}".strip()
            tokens = tokenize(search_text)
            counts = Counter(tokens)
            exact_terms = extract_exact_terms(tokens)
            docs.append(
                {
                    "doc_id": doc_id,
                    "topic_id": post.get("topic_id"),
                    "post_id": post.get("post_id"),
                    "source_url": post.get("source_url"),
                    "title": title,
                    "text": text,
                    "search_text": search_text,
                    "exact_text": " ".join(tokens),
                    "exact_terms": exact_terms,
                    "tokens": sum(counts.values()),
                }
            )
            for token, count in counts.items():
                inverted[token].append({"doc_id": doc_id, "count": count})
            for token in exact_terms:
                exact[token].append(doc_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "keyword_index.json"
    payload = {
        "schema": "aoa_4pda_keyword_index_v1",
        "profile_id": profile_id,
        "scoring": {
            "algorithm": "bm25_exact_v1",
            "bm25_k1": 1.5,
            "bm25_b": 0.75,
            "exact_term_boost": 1.75,
            "phrase_boost": 2.5,
        },
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "doc_count": len(docs),
        "term_count": len(inverted),
        "docs": docs,
        "inverted": inverted,
        "exact": exact,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _is_exact_term(token: str) -> bool:
    return any(char.isdigit() for char in token) or any(separator in token for separator in [".", "_", "/", "-"])
