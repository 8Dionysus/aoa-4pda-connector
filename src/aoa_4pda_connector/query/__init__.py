"""Query helpers over the tiny starter keyword index."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.index import extract_exact_terms, technical_alias_tokens, tokenize
from aoa_4pda_connector.vector import query_vector_index


BM25_K1 = 1.5
BM25_B = 0.75
EXACT_TERM_BOOST = 1.75
PHRASE_BOOST = 2.5
GRAPH_RELATION_WEIGHT = 0.85
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
ROOT_INTENT_TERMS = {"boot.img", "init_boot.img", "kernelsu", "ksu", "magisk", "root"}
ROOT_RELATION_EDGE_KINDS = {"root_mentions_firmware", "root_targets_file", "root_uses_tool"}
RECOVERY_INTENT_TERMS = {"orangefox", "recovery", "recovery.img", "twrp", "vendor_boot"}
RECOVERY_RELATION_EDGE_KINDS = {
    "recovery_mentions_firmware",
    "recovery_targets_file",
    "recovery_uses_tool",
}


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
                "posted_at": doc.get("posted_at"),
                "captured_at": doc.get("captured_at"),
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

    results = packet.get("results", [])
    for rank, result in enumerate(results, start=1):
        result["keyword_rank"] = rank
        result["graph_context"] = _graph_context_for_result(result, nodes, edges)

    query_report = packet.get("query_report", {})
    intents = _relation_intents(query_report)
    reranked_results = _rerank_graph_results(results, intents, _relation_query_values(query_report))
    for rank, result in enumerate(reranked_results, start=1):
        result["graph_rank"] = rank
    packet["results"] = reranked_results

    packet["policy"]["source"] = "local_keyword_index_plus_graph"
    packet["graph_report"] = {
        "graph_path": str(graph_path),
        "node_count": graph.get("node_count", 0),
        "edge_count": graph.get("edge_count", 0),
        "rerank": {
            "algorithm": "relation_intent_v1",
            "applied": bool(intents),
            "intents": sorted(intents),
        },
        "relation_edge_kinds": sorted(
            {
                str(edge.get("kind"))
                for edge in edges
                if edge.get("kind") in RELATION_EDGE_KINDS
            }
        ),
    }
    return packet


def query_hybrid_packet(
    index_path: Path,
    vector_path: Path,
    graph_path: Path | None,
    query: str,
    limit: int = 5,
    *,
    keyword_weight: float = 0.65,
    vector_weight: float = 0.35,
    graph_weight: float = GRAPH_RELATION_WEIGHT,
) -> dict[str, object]:
    """Return keyword+vector evidence results, optionally enriched with graph context."""

    candidate_limit = max(limit * 4, 80)
    keyword_packet = (
        query_graph_packet(index_path, graph_path, query, limit=candidate_limit)
        if graph_path is not None
        else query_keyword_index(index_path, query, limit=candidate_limit)
    )
    vector_packet = query_vector_index(vector_path, query, limit=candidate_limit)
    keyword_results = _ranked_result_map(keyword_packet.get("results", []), "keyword_rank")
    vector_results = _ranked_result_map(vector_packet.get("results", []), "vector_rank")
    keyword_max = max([float(result.get("score") or 0.0) for result in keyword_results.values()] or [1.0])
    vector_max = max([float(result.get("score") or 0.0) for result in vector_results.values()] or [1.0])

    graph_enabled = graph_path is not None
    effective_graph_weight = graph_weight if graph_enabled else 0.0
    pending: list[dict[str, object]] = []
    for key in sorted(set(keyword_results) | set(vector_results)):
        keyword_result = keyword_results.get(key, {})
        vector_result = vector_results.get(key, {})
        base = dict(keyword_result or vector_result)
        keyword_score = float(keyword_result.get("score") or 0.0)
        vector_score = float(vector_result.get("score") or 0.0)
        keyword_normalized = keyword_score / keyword_max if keyword_max else 0.0
        vector_normalized = vector_score / vector_max if vector_max else 0.0
        graph_raw = _graph_relation_score(keyword_result)
        pending.append(
            {
                "base": base,
                "keyword_score": keyword_score,
                "vector_score": vector_score,
                "keyword_normalized": keyword_normalized,
                "vector_normalized": vector_normalized,
                "graph_raw": graph_raw,
                "keyword_result": keyword_result,
                "vector_result": vector_result,
            }
        )

    graph_max = max([float(item["graph_raw"]) for item in pending] or [0.0])
    combined: list[dict[str, object]] = []
    for item in pending:
        base = item["base"]
        keyword_score = float(item["keyword_score"])
        vector_score = float(item["vector_score"])
        keyword_normalized = float(item["keyword_normalized"])
        vector_normalized = float(item["vector_normalized"])
        graph_raw = float(item["graph_raw"])
        graph_normalized = graph_raw / graph_max if graph_max else 0.0
        relation_boost = effective_graph_weight * graph_normalized
        hybrid_without_graph = keyword_weight * keyword_normalized + vector_weight * vector_normalized
        hybrid_score = hybrid_without_graph + relation_boost
        base["score"] = round(hybrid_score, 6)
        base["score_breakdown"] = {
            "hybrid": round(hybrid_score, 6),
            "hybrid_without_graph": round(hybrid_without_graph, 6),
            "keyword_raw": round(keyword_score, 6),
            "keyword_normalized": round(keyword_normalized, 6),
            "vector_raw": round(vector_score, 6),
            "vector_normalized": round(vector_normalized, 6),
            "graph_raw": round(graph_raw, 6),
            "graph_normalized": round(graph_normalized, 6),
            "graph_relation_boost": round(relation_boost, 6),
            "keyword_weight": keyword_weight,
            "vector_weight": vector_weight,
            "graph_weight": effective_graph_weight,
        }
        keyword_result = item["keyword_result"]
        vector_result = item["vector_result"]
        base["keyword_rank"] = keyword_result.get("keyword_rank")
        base["vector_rank"] = vector_result.get("vector_rank")
        base["vector_algorithm"] = vector_result.get("vector_algorithm")
        if vector_result.get("sample_features") and not base.get("vector_sample_features"):
            base["vector_sample_features"] = vector_result.get("sample_features")
        combined.append(base)

    ranked = sorted(combined, key=_hybrid_ranking_key)
    for rank, result in enumerate(ranked, start=1):
        result["hybrid_rank"] = rank

    packet = {
        "schema": "aoa_4pda_evidence_packet_v1",
        "packet_id": packet_id_for_query(query),
        "query": query,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "query_report": {
            "algorithm": "hybrid_bm25_vector_graph_v1" if graph_enabled else "hybrid_bm25_vector_v1",
            "unit": keyword_packet.get("query_report", {}).get("unit", "chunk"),
            "keyword_weight": keyword_weight,
            "vector_weight": vector_weight,
            "graph_weight": effective_graph_weight,
            "keyword": keyword_packet.get("query_report", {}),
            "vector": vector_packet.get("query_report", {}),
        },
        "hybrid_report": {
            "algorithm": (
                "weighted_normalized_keyword_vector_relation_boost_v1"
                if graph_enabled
                else "weighted_normalized_keyword_vector_v1"
            ),
            "keyword_path": str(index_path),
            "vector_path": str(vector_path),
            "graph_path": str(graph_path) if graph_path else None,
            "candidate_limit": candidate_limit,
            "result_count": len(ranked[:limit]),
            "graph_relation_boost": {
                "algorithm": "relation_intent_saturation_v1",
                "enabled": graph_enabled,
                "weight": effective_graph_weight,
                "max_raw": round(graph_max, 6),
            },
        },
        "vector_report": vector_packet.get("vector_report", {}),
        "results": ranked[:limit],
        "policy": {
            "source": "local_keyword_vector_index_plus_graph" if graph_path else "local_keyword_vector_index",
            "internal_search_used": False,
        },
    }
    if graph_path is not None and "graph_report" in keyword_packet:
        packet["graph_report"] = keyword_packet["graph_report"]
    return packet


def _relation_intents(query_report: object) -> set[str]:
    if not isinstance(query_report, dict):
        return set()
    values = {
        str(value).casefold()
        for field in ["terms", "exact_terms", "specific_terms", "technical_terms"]
        for value in query_report.get(field, [])
    }
    intents: set[str] = set()
    if values.intersection(ROOT_INTENT_TERMS):
        intents.add("root")
    if values.intersection(RECOVERY_INTENT_TERMS):
        intents.add("recovery")
    return intents


def _ranked_result_map(results: object, rank_field: str) -> dict[str, dict[str, object]]:
    if not isinstance(results, list):
        return {}
    mapped: dict[str, dict[str, object]] = {}
    for rank, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            continue
        key = str(result.get("chunk_id") or result.get("post_id") or "")
        if not key:
            continue
        value = dict(result)
        value.setdefault(rank_field, rank)
        mapped[key] = value
    return mapped


def _hybrid_ranking_key(result: dict[str, object]) -> tuple[object, ...]:
    breakdown = result.get("score_breakdown", {})
    if not isinstance(breakdown, dict):
        breakdown = {}
    keyword_rank = result.get("keyword_rank")
    vector_rank = result.get("vector_rank")
    return (
        -float(result.get("score") or 0.0),
        -float(breakdown.get("graph_normalized") or 0.0),
        int(keyword_rank) if keyword_rank else 999999,
        int(vector_rank) if vector_rank else 999999,
        -float(breakdown.get("keyword_raw") or 0.0),
        -float(breakdown.get("vector_raw") or 0.0),
    )


def _graph_relation_score(result: dict[str, object]) -> float:
    summary = result.get("relation_rerank", {})
    if not isinstance(summary, dict):
        return 0.0
    edge_count = int(summary.get("matching_edge_count") or 0)
    relation_kinds = summary.get("matching_relation_kinds", [])
    kind_count = len(relation_kinds) if isinstance(relation_kinds, list) else 0
    if edge_count <= 0 or kind_count <= 0:
        return 0.0
    confidence_sum = float(summary.get("matching_relation_confidence_sum") or 0.0)
    edge_component = min(edge_count, 2) / 2
    kind_component = min(kind_count, 2) / 2
    confidence_component = min(confidence_sum, 1.0)
    return round(0.4 * edge_component + 0.4 * kind_component + 0.2 * confidence_component, 6)


def _relation_query_values(query_report: object) -> set[str]:
    if not isinstance(query_report, dict):
        return set()
    values = {
        _normalize_relation_value(value)
        for field in ["exact_terms", "specific_terms", "technical_terms"]
        for value in query_report.get(field, [])
    }
    return {value for value in values if len(value) >= 3}


def _rerank_graph_results(
    results: object,
    intents: set[str],
    query_values: set[str],
) -> list[dict[str, object]]:
    if not isinstance(results, list):
        return []
    typed_results = [result for result in results if isinstance(result, dict)]
    if not intents:
        for result in typed_results:
            result["relation_rerank"] = _relation_rerank_summary(result, intents, query_values)
        return typed_results
    for result in typed_results:
        result["relation_rerank"] = _relation_rerank_summary(result, intents, query_values)
    return sorted(typed_results, key=_relation_rerank_key)


def _relation_rerank_summary(
    result: dict[str, object],
    intents: set[str],
    query_values: set[str],
) -> dict[str, object]:
    desired_kinds = _desired_relation_kinds(intents)
    relation_edges = _result_relation_edges(result)
    matching_edges = [
        edge
        for edge in relation_edges
        if edge.get("kind") in desired_kinds
        and _relation_edge_matches_query(edge, query_values)
    ]
    confidence_sum = sum(float(edge.get("confidence") or 0.0) for edge in matching_edges)
    return {
        "intents": sorted(intents),
        "query_values": sorted(query_values),
        "matching_edge_count": len(matching_edges),
        "matching_relation_kinds": sorted({str(edge.get("kind")) for edge in matching_edges}),
        "matching_relation_confidence_sum": round(confidence_sum, 6),
    }


def _relation_rerank_key(result: dict[str, object]) -> tuple[object, ...]:
    summary = result.get("relation_rerank", {})
    if not isinstance(summary, dict):
        summary = {}
    keyword_rank = int(result.get("keyword_rank") or 0)
    return (
        -int(summary.get("matching_edge_count") or 0),
        -len(summary.get("matching_relation_kinds", [])),
        -float(summary.get("matching_relation_confidence_sum") or 0.0),
        -len(result.get("matched_specific_terms", [])),
        -len(result.get("matched_exact_terms", [])),
        -float(result.get("score") or 0.0),
        keyword_rank,
    )


def _desired_relation_kinds(intents: set[str]) -> set[str]:
    kinds: set[str] = set()
    if "root" in intents:
        kinds.update(ROOT_RELATION_EDGE_KINDS)
    if "recovery" in intents:
        kinds.update(RECOVERY_RELATION_EDGE_KINDS)
    return kinds


def _result_relation_edges(result: dict[str, object]) -> list[dict[str, object]]:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        return []
    edges = context.get("relation_edges", [])
    return [edge for edge in edges if isinstance(edge, dict)]


def _relation_edge_matches_query(edge: dict[str, object], query_values: set[str]) -> bool:
    if not query_values:
        return True
    kind = str(edge.get("kind", ""))
    if kind.endswith("_uses_tool") or kind.endswith("_targets_file") or kind.endswith("_mentions_firmware"):
        edge_text = _normalize_relation_value(edge.get("to_node", ""))
    else:
        edge_text = _normalize_relation_value(
            f"{edge.get('kind', '')} {edge.get('from_node', '')} {edge.get('to_node', '')}"
        )
    return any(value in edge_text for value in query_values)


def _normalize_relation_value(value: object) -> str:
    return str(value).casefold().replace("_", " ").replace("-", " ")


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
