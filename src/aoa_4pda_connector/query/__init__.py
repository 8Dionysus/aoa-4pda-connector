"""Query helpers over the tiny starter keyword index."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.index import tokenize


def query_keyword_index(index_path: Path, query: str, limit: int = 5) -> dict[str, object]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    terms = tokenize(query)
    scores: Counter[str] = Counter()
    for term in terms:
        for hit in index.get("inverted", {}).get(term, []):
            scores[hit["doc_id"]] += int(hit["count"])
    docs = {doc["doc_id"]: doc for doc in index.get("docs", [])}
    results = []
    for doc_id, score in scores.most_common(limit):
        doc = docs[doc_id]
        text = str(doc.get("text", ""))
        results.append(
            {
                "source_url": doc.get("source_url"),
                "topic_id": doc.get("topic_id"),
                "post_id": doc.get("post_id"),
                "snippet": text[:500],
                "score": float(score),
                "evidence_refs": [f"post:{doc.get('post_id')}"],
            }
        )
    return {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": f"query-{abs(hash(query))}",
        "query": query,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "results": results,
        "policy": {
            "source": "local_keyword_index",
            "internal_search_used": False,
        },
    }
