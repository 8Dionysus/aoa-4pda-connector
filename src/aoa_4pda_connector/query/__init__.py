"""Query helpers over the tiny starter keyword index."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.index import extract_exact_terms, tokenize


BM25_K1 = 1.5
BM25_B = 0.75
EXACT_TERM_BOOST = 1.75
PHRASE_BOOST = 2.5


def query_keyword_index(index_path: Path, query: str, limit: int = 5) -> dict[str, object]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    terms = tokenize(query)
    exact_terms = extract_exact_terms(terms)
    phrase_candidates = _phrase_candidates(terms)
    docs = {doc["doc_id"]: doc for doc in index.get("docs", [])}
    doc_count = max(1, int(index.get("doc_count", len(docs))))
    avg_doc_len = _average_doc_length(docs.values())
    doc_scores: dict[str, dict[str, object]] = {}

    for term in terms:
        hits = index.get("inverted", {}).get(term, [])
        if not hits:
            continue
        idf = math.log(1 + (doc_count - len(hits) + 0.5) / (len(hits) + 0.5))
        for hit in hits:
            doc_id = str(hit["doc_id"])
            doc = docs[doc_id]
            tf = int(hit["count"])
            doc_len = max(1, int(doc.get("tokens", 0)))
            bm25 = idf * ((tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / avg_doc_len)))
            entry = doc_scores.setdefault(
                doc_id,
                {"bm25": 0.0, "exact": 0.0, "phrase": 0.0, "matched_terms": set(), "matched_exact_terms": set(), "matched_phrases": set()},
            )
            entry["bm25"] += bm25
            entry["matched_terms"].add(term)

    for term in exact_terms:
        for doc_id in index.get("exact", {}).get(term, []):
            entry = doc_scores.setdefault(
                doc_id,
                {"bm25": 0.0, "exact": 0.0, "phrase": 0.0, "matched_terms": set(), "matched_exact_terms": set(), "matched_phrases": set()},
            )
            entry["exact"] += EXACT_TERM_BOOST
            entry["matched_exact_terms"].add(term)

    for phrase in phrase_candidates:
        for doc_id, doc in docs.items():
            if phrase in str(doc.get("exact_text", "")):
                entry = doc_scores.setdefault(
                    doc_id,
                    {"bm25": 0.0, "exact": 0.0, "phrase": 0.0, "matched_terms": set(), "matched_exact_terms": set(), "matched_phrases": set()},
                )
                entry["phrase"] += PHRASE_BOOST
                entry["matched_phrases"].add(phrase)

    results = []
    ranked = sorted(
        doc_scores.items(),
        key=lambda item: (
            float(item[1]["bm25"]) + float(item[1]["exact"]) + float(item[1]["phrase"]),
            len(item[1]["matched_exact_terms"]),
            len(item[1]["matched_phrases"]),
        ),
        reverse=True,
    )
    for doc_id, score in ranked[:limit]:
        doc = docs[doc_id]
        text = str(doc.get("text", ""))
        score_total = float(score["bm25"]) + float(score["exact"]) + float(score["phrase"])
        matched_terms = sorted(score["matched_terms"])
        matched_exact_terms = sorted(score["matched_exact_terms"])
        matched_phrases = sorted(score["matched_phrases"])
        results.append(
            {
                "source_url": doc.get("source_url"),
                "topic_id": doc.get("topic_id"),
                "post_id": doc.get("post_id"),
                "snippet": _focused_snippet(text, matched_exact_terms + matched_terms),
                "score": round(score_total, 6),
                "score_breakdown": {
                    "bm25": round(float(score["bm25"]), 6),
                    "exact": round(float(score["exact"]), 6),
                    "phrase": round(float(score["phrase"]), 6),
                },
                "matched_terms": matched_terms,
                "matched_exact_terms": matched_exact_terms,
                "matched_phrases": matched_phrases,
                "evidence_refs": [f"post:{doc.get('post_id')}"],
            }
        )
    return {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": f"query-{abs(hash(query))}",
        "query": query,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "query_report": {
            "algorithm": "bm25_exact_v1",
            "terms": terms,
            "exact_terms": exact_terms,
            "phrase_candidates": phrase_candidates,
            "bm25": {"k1": BM25_K1, "b": BM25_B},
            "boosts": {"exact_term": EXACT_TERM_BOOST, "phrase": PHRASE_BOOST},
        },
        "results": results,
        "policy": {
            "source": "local_keyword_index",
            "internal_search_used": False,
        },
    }


def _average_doc_length(docs: object) -> float:
    lengths = [max(1, int(doc.get("tokens", 0))) for doc in docs]
    return sum(lengths) / len(lengths) if lengths else 1.0


def _phrase_candidates(terms: list[str]) -> list[str]:
    phrases: list[str] = []
    for size in range(2, min(5, len(terms)) + 1):
        for start in range(0, len(terms) - size + 1):
            window = terms[start : start + size]
            phrase = " ".join(window)
            if any(any(char.isdigit() for char in term) for term in window) and phrase not in phrases:
                phrases.append(phrase)
    return phrases


def _focused_snippet(text: str, needles: list[str], radius: int = 190) -> str:
    if not text:
        return ""
    lowered = text.lower()
    starts = [lowered.find(needle.lower()) for needle in needles if needle and lowered.find(needle.lower()) >= 0]
    if not starts:
        return text[:500]
    center = min(starts)
    start = max(0, center - radius)
    end = min(len(text), center + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"
