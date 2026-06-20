"""Query helpers over the tiny starter keyword index."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.index import extract_exact_terms, technical_alias_tokens, tokenize


BM25_K1 = 1.5
BM25_B = 0.75
EXACT_TERM_BOOST = 1.75
PHRASE_BOOST = 2.5
RELATION_EDGE_KINDS = (
    "fixes_issue",
    "recovery_mentions_firmware",
    "recovery_targets_file",
    "recovery_uses_tool",
    "root_mentions_firmware",
    "root_targets_file",
    "root_uses_tool",
    "warns_about",
)


def packet_id_for_query(query: str) -> str:
    digest = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()
    return f"query-{digest[:16]}"


def query_keyword_index(index_path: Path, query: str, limit: int = 5) -> dict[str, object]:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    terms = tokenize(query)
    technical_terms = technical_alias_tokens(query)
    exact_terms = extract_exact_terms(terms)
    phrase_candidates = _phrase_candidates(terms)
    docs = {doc["doc_id"]: doc for doc in index.get("docs", [])}
    doc_count = max(1, int(index.get("doc_count", len(docs))))
    specific_terms = _specific_query_terms(terms, exact_terms, index, doc_count)
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
    ranked = sorted(doc_scores.items(), key=lambda item: _ranking_key(item, specific_terms), reverse=True)
    for doc_id, score in ranked[:limit]:
        doc = docs[doc_id]
        text = str(doc.get("text", ""))
        score_total = float(score["bm25"]) + float(score["exact"]) + float(score["phrase"])
        matched_terms = sorted(score["matched_terms"])
        matched_exact_terms = sorted(score["matched_exact_terms"])
        matched_phrases = sorted(score["matched_phrases"])
        matched_specific_terms = sorted(_matched_specific_terms(score, specific_terms))
        results.append(
            {
                "source_url": doc.get("source_url"),
                "topic_id": doc.get("topic_id"),
                "post_id": doc.get("post_id"),
                "chunk_id": doc.get("chunk_id", doc_id),
                "chunk_index": doc.get("chunk_index"),
                "char_start": doc.get("char_start"),
                "char_end": doc.get("char_end"),
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
                "matched_specific_terms": matched_specific_terms,
                "evidence_refs": [f"chunk:{doc.get('chunk_id', doc_id)}", f"post:{doc.get('post_id')}"],
            }
        )
    return {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": packet_id_for_query(query),
        "query": query,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "query_report": {
            "algorithm": "bm25_exact_v1",
            "unit": index.get("unit", "post"),
            "terms": terms,
            "technical_terms": technical_terms,
            "exact_terms": exact_terms,
            "specific_terms": specific_terms,
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


def query_graph_packet(index_path: Path, graph_path: Path, query: str, limit: int = 5) -> dict[str, object]:
    """Return keyword results enriched with starter graph relation context."""

    packet = query_keyword_index(index_path, query, limit)
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes = {str(node.get("node_id")): node for node in graph.get("nodes", [])}
    edges = [edge for edge in graph.get("edges", [])]

    for result in packet.get("results", []):
        result["graph_context"] = _graph_context_for_result(result, nodes, edges)

    packet["policy"]["source"] = "local_keyword_index_plus_graph"
    packet["graph_report"] = {
        "graph_path": str(graph_path),
        "node_count": graph.get("node_count", 0),
        "edge_count": graph.get("edge_count", 0),
        "relation_edge_kinds": sorted(
            {
                str(edge.get("kind"))
                for edge in edges
                if edge.get("kind") in RELATION_EDGE_KINDS
            }
        ),
    }
    return packet


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


def _specific_query_terms(
    terms: list[str],
    exact_terms: list[str],
    index: dict[str, object],
    doc_count: int,
) -> list[str]:
    inverted = index.get("inverted", {})
    rare_cutoff = max(3, int(doc_count * 0.08))
    specific: list[str] = []
    for term in terms:
        if term.isdigit():
            continue
        hits = inverted.get(term, []) if isinstance(inverted, dict) else []
        is_rare = 0 < len(hits) <= rare_cutoff
        is_structured = term in exact_terms and any(separator in term for separator in [".", "_", "/", "-"])
        if (is_rare or is_structured) and term not in specific:
            specific.append(term)
    return specific


def _matched_specific_terms(score: dict[str, object], specific_terms: list[str]) -> set[str]:
    matched_terms = set(score["matched_terms"])
    matched_exact_terms = set(score["matched_exact_terms"])
    return (matched_terms | matched_exact_terms).intersection(specific_terms)


def _ranking_key(item: tuple[str, dict[str, object]], specific_terms: list[str]) -> tuple[float, int, int, float]:
    score = item[1]
    total = float(score["bm25"]) + float(score["exact"]) + float(score["phrase"])
    return (
        float(len(_matched_specific_terms(score, specific_terms))),
        len(score["matched_exact_terms"]),
        len(score["matched_phrases"]),
        total,
    )


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


def _graph_context_for_result(
    result: dict[str, object],
    nodes: dict[str, dict[str, object]],
    edges: list[dict[str, object]],
) -> dict[str, object]:
    post_id = result.get("post_id")
    post_node = f"post:{post_id}" if post_id is not None else ""
    source_url = str(result.get("source_url", ""))
    mention_edges = [
        edge
        for edge in edges
        if edge.get("kind") == "post_mentions_entity"
        and edge.get("from_node") == post_node
        and _source_refs_include(edge, source_url)
    ]
    entity_node_ids = sorted({str(edge.get("to_node")) for edge in mention_edges if edge.get("to_node")})
    entity_node_set = set(entity_node_ids)
    relation_edges = [
        _edge_summary(edge)
        for edge in edges
        if edge.get("kind") in RELATION_EDGE_KINDS
        and _source_refs_include(edge, source_url)
        and (
            str(edge.get("from_node")) in entity_node_set
            or str(edge.get("to_node")) in entity_node_set
        )
    ]
    relation_endpoint_ids = {
        node_id
        for edge in relation_edges
        for node_id in [str(edge.get("from_node")), str(edge.get("to_node"))]
        if node_id
    }
    context_node_ids = sorted(entity_node_set.union(relation_endpoint_ids))
    fixes_issue = _relation_targets_by_from(relation_edges, "fixes_issue")
    warns_about = _relation_targets_by_from(relation_edges, "warns_about")
    warned_target_ids = sorted({target for targets in warns_about.values() for target in targets})

    return {
        "post_node": post_node,
        "source_refs": [source_url] if source_url else [],
        "entity_node_ids": entity_node_ids,
        "relation_edges": relation_edges,
        "issues": [
            _node_summary(nodes[node_id])
            for node_id in context_node_ids
            if node_id in nodes and nodes[node_id].get("kind") == "issue"
        ],
        "fixes": [
            {**_node_summary(nodes[node_id]), "fixes_issue_node_ids": fixes_issue.get(node_id, [])}
            for node_id in sorted(fixes_issue)
            if node_id in nodes
        ],
        "warnings": [
            {**_node_summary(nodes[node_id]), "warns_about_node_ids": warns_about.get(node_id, [])}
            for node_id in sorted(warns_about)
            if node_id in nodes
        ],
        "warned_targets": [
            _node_summary(nodes[node_id])
            for node_id in warned_target_ids
            if node_id in nodes
        ],
    }


def _relation_targets_by_from(edges: list[dict[str, object]], kind: str) -> dict[str, list[str]]:
    targets: dict[str, list[str]] = {}
    for edge in edges:
        if edge.get("kind") != kind:
            continue
        from_node = str(edge.get("from_node"))
        to_node = str(edge.get("to_node"))
        if not from_node or not to_node:
            continue
        values = targets.setdefault(from_node, [])
        if to_node not in values:
            values.append(to_node)
    return {node_id: sorted(values) for node_id, values in targets.items()}


def _node_summary(node: dict[str, object]) -> dict[str, object]:
    return {
        "node_id": node.get("node_id"),
        "kind": node.get("kind"),
        "label": node.get("label"),
        "source_refs": node.get("source_refs", []),
        "confidence": node.get("confidence"),
    }


def _edge_summary(edge: dict[str, object]) -> dict[str, object]:
    return {
        "edge_id": edge.get("edge_id"),
        "kind": edge.get("kind"),
        "from_node": edge.get("from_node"),
        "to_node": edge.get("to_node"),
        "source_refs": edge.get("source_refs", []),
        "confidence": edge.get("confidence"),
    }


def _source_refs_include(item: dict[str, object], source_url: str) -> bool:
    if not source_url:
        return True
    return any(str(ref) == source_url for ref in item.get("source_refs", []))
