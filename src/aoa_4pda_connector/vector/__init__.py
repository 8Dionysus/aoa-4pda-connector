"""Deterministic local vector index for no-model semantic-lite retrieval."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.chunk import chunk_post
from aoa_4pda_connector.index import tokenize


DEFAULT_DIMENSIONS = 256


def build_vector_index(
    normalized_dir: Path,
    output_dir: Path,
    profile_id: str = "starter",
    *,
    dimensions: int = DEFAULT_DIMENSIONS,
) -> Path:
    """Build a compact hashed-vector index from normalized topic/post chunks.

    The starter adapter deliberately avoids model downloads and API keys. It is
    a stable vector contract for paraphrase-ish recall that can later be
    swapped for a stronger embedding backend without changing storage routes.
    """

    docs: list[dict[str, object]] = []
    feature_names: set[str] = set()
    for topic_path in sorted(normalized_dir.glob("topic-*.json")):
        topic = json.loads(topic_path.read_text(encoding="utf-8"))
        title = str(topic.get("title", ""))
        for post in topic.get("posts", []):
            for chunk in chunk_post(post):
                text = str(chunk.get("text", ""))
                doc_id = str(chunk["chunk_id"])
                search_text = f"{title} {text}".strip()
                vector, features = text_vector(search_text, dimensions=dimensions)
                feature_names.update(features)
                docs.append(
                    {
                        "doc_id": doc_id,
                        "chunk_id": chunk["chunk_id"],
                        "chunk_index": chunk["chunk_index"],
                        "char_start": chunk["char_start"],
                        "char_end": chunk["char_end"],
                        "topic_id": post.get("topic_id"),
                        "post_id": post.get("post_id"),
                        "source_url": post.get("source_url"),
                        "posted_at": post.get("posted_at"),
                        "captured_at": post.get("captured_at"),
                        "title": title,
                        "text": text,
                        "search_text": search_text,
                        "vector": vector,
                        "feature_count": len(features),
                        "sample_features": features[:24],
                    }
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "vector_index.json"
    payload = {
        "schema": "aoa_4pda_vector_index_v1",
        "profile_id": profile_id,
        "unit": "chunk",
        "algorithm": "hashed_char_ngram_vector_v1",
        "dimensions": dimensions,
        "built_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "doc_count": len(docs),
        "feature_count": len(feature_names),
        "docs": docs,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def query_vector_index(vector_path: Path, query: str, limit: int = 5) -> dict[str, object]:
    """Query a hashed vector index and return an evidence-packet-shaped result."""

    index = json.loads(vector_path.read_text(encoding="utf-8"))
    dimensions = int(index.get("dimensions") or DEFAULT_DIMENSIONS)
    query_vector, query_features = text_vector(query, dimensions=dimensions)
    scored: list[tuple[float, dict[str, object]]] = []
    for doc in index.get("docs", []):
        score = _dot(query_vector, _vector_dict(doc.get("vector", [])))
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: item[0], reverse=True)

    results = []
    needle_terms = [feature.split(":", 1)[1] for feature in query_features if feature.startswith("tok:")]
    for rank, (score, doc) in enumerate(scored[:limit], start=1):
        doc_id = str(doc.get("doc_id") or doc.get("chunk_id"))
        results.append(
            {
                "source_url": doc.get("source_url"),
                "topic_id": doc.get("topic_id"),
                "post_id": doc.get("post_id"),
                "posted_at": doc.get("posted_at"),
                "captured_at": doc.get("captured_at"),
                "chunk_id": doc.get("chunk_id", doc_id),
                "chunk_index": doc.get("chunk_index"),
                "char_start": doc.get("char_start"),
                "char_end": doc.get("char_end"),
                "snippet": _focused_snippet(str(doc.get("text", "")), needle_terms),
                "score": round(score, 6),
                "score_breakdown": {"vector": round(score, 6)},
                "vector_rank": rank,
                "vector_algorithm": index.get("algorithm"),
                "sample_features": doc.get("sample_features", []),
                "evidence_refs": [f"chunk:{doc.get('chunk_id', doc_id)}", f"post:{doc.get('post_id')}"],
            }
        )
    return {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": _packet_id_for_query(query),
        "query": query,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "query_report": {
            "algorithm": "hashed_char_ngram_vector_v1",
            "unit": index.get("unit", "chunk"),
            "dimensions": dimensions,
            "query_feature_count": len(query_features),
            "query_sample_features": query_features[:24],
        },
        "vector_report": {
            "vector_path": str(vector_path),
            "algorithm": index.get("algorithm"),
            "doc_count": index.get("doc_count", 0),
            "feature_count": index.get("feature_count", 0),
            "dimensions": dimensions,
        },
        "results": results,
        "policy": {
            "source": "local_hashed_vector_index",
            "internal_search_used": False,
        },
    }


def text_vector(text: str, *, dimensions: int = DEFAULT_DIMENSIONS) -> tuple[dict[str, float], list[str]]:
    features = semantic_features(text)
    counts = Counter(features)
    buckets: dict[int, float] = {}
    for feature, count in counts.items():
        index, sign = _feature_bucket(feature, dimensions)
        weight = _feature_weight(feature) * count * sign
        buckets[index] = buckets.get(index, 0.0) + weight
    norm = math.sqrt(sum(value * value for value in buckets.values())) or 1.0
    vector = {str(index): round(value / norm, 6) for index, value in sorted(buckets.items()) if value}
    return vector, sorted(counts)


def semantic_features(text: str) -> list[str]:
    tokens = tokenize(text)
    features: list[str] = []
    for token in tokens:
        features.append(f"tok:{token}")
        normalized = token.replace("_", "").replace("-", "").replace(".", "")
        if len(normalized) >= 5:
            features.extend(f"tri:{normalized[index:index + 3]}" for index in range(len(normalized) - 2))
        if len(normalized) >= 7:
            features.extend(f"quad:{normalized[index:index + 4]}" for index in range(len(normalized) - 3))
    return features


def _feature_bucket(feature: str, dimensions: int) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    number = int.from_bytes(digest, "big")
    return number % dimensions, 1.0 if number & 1 else -1.0


def _packet_id_for_query(query: str) -> str:
    digest = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
    return f"query-{digest[:16]}"


def _feature_weight(feature: str) -> float:
    if feature.startswith("tok:"):
        return 1.0
    if feature.startswith("quad:"):
        return 0.45
    return 0.3


def _vector_dict(raw: object) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    return {str(key): float(value) for key, value in raw.items()}


def _dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _focused_snippet(text: str, needles: list[str], radius: int = 190) -> str:
    if not text:
        return ""
    lowered = text.casefold()
    starts = [lowered.find(needle.casefold()) for needle in needles if needle and lowered.find(needle.casefold()) >= 0]
    if not starts:
        return text[:500]
    center = min(starts)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"
