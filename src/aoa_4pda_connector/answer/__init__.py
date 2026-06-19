"""Answer rendering over local evidence packets."""

from __future__ import annotations


def render_answer_packet(evidence_packet: dict[str, object], limit: int = 5) -> dict[str, object]:
    """Render a compact answer packet from a graph-enriched evidence packet."""

    policy = evidence_packet.get("policy", {})
    internal_search_used = bool(policy.get("internal_search_used")) if isinstance(policy, dict) else False
    answers = [
        _answer_for_result(result)
        for result in evidence_packet.get("results", [])[:limit]
    ]
    return {
        "schema": "aoa_4pda_answer_packet_v1",
        "answer_id": str(evidence_packet.get("packet_id", "query")).replace("query-", "answer-", 1),
        "query": evidence_packet.get("query", ""),
        "created_at": evidence_packet.get("created_at"),
        "answer_report": {
            "renderer": "starter_graph_context_v1",
            "source_packet_id": evidence_packet.get("packet_id"),
            "source_packet_schema": evidence_packet.get("schema"),
            "query_algorithm": evidence_packet.get("query_report", {}).get("algorithm")
            if isinstance(evidence_packet.get("query_report"), dict)
            else None,
            "graph_context_required": True,
        },
        "answers": answers,
        "policy": {
            "source": "local_keyword_index_plus_graph_answer_renderer",
            "internal_search_used": internal_search_used,
        },
    }


def _answer_for_result(result: dict[str, object]) -> dict[str, object]:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        context = {}
    issue_labels = _labels(context.get("issues", []))
    fix_labels = _labels(context.get("fixes", []))
    warning_labels = _labels(context.get("warnings", []))
    warned_target_labels = _labels(context.get("warned_targets", []))
    answer_kind = _answer_kind(issue_labels, fix_labels, warning_labels)
    relation_edges = context.get("relation_edges", [])
    if not isinstance(relation_edges, list):
        relation_edges = []

    return {
        "answer_kind": answer_kind,
        "answer_text": _answer_text(result, issue_labels, fix_labels, warning_labels, warned_target_labels),
        "source_url": result.get("source_url"),
        "topic_id": result.get("topic_id"),
        "post_id": result.get("post_id"),
        "chunk_id": result.get("chunk_id"),
        "score": result.get("score"),
        "score_breakdown": result.get("score_breakdown", {}),
        "issue_labels": issue_labels,
        "fix_labels": fix_labels,
        "warning_labels": warning_labels,
        "warned_target_labels": warned_target_labels,
        "evidence_refs": result.get("evidence_refs", []),
        "source_refs": context.get("source_refs", []) or ([result.get("source_url")] if result.get("source_url") else []),
        "confidence": {
            "basis": "starter_graph_context" if context else "keyword_result",
            "relation_confidence_min": _min_confidence(relation_edges),
            "result_score": result.get("score"),
        },
    }


def _answer_kind(issue_labels: list[str], fix_labels: list[str], warning_labels: list[str]) -> str:
    if issue_labels and fix_labels and warning_labels:
        return "issue_fix_warning"
    if issue_labels and fix_labels:
        return "issue_fix"
    if warning_labels:
        return "warning"
    return "snippet"


def _answer_text(
    result: dict[str, object],
    issue_labels: list[str],
    fix_labels: list[str],
    warning_labels: list[str],
    warned_target_labels: list[str],
) -> str:
    parts: list[str] = []
    if issue_labels:
        parts.append(f"Issue: {_join_labels(issue_labels)}.")
    if fix_labels:
        parts.append(f"Suggested fixes: {_join_labels(fix_labels)}.")
    if warning_labels:
        warning_text = f"Warnings: {_join_labels(warning_labels)}"
        if warned_target_labels:
            warning_text = f"{warning_text} (about: {_join_labels(warned_target_labels)})"
        parts.append(f"{warning_text}.")
    if not parts:
        snippet = str(result.get("snippet", "")).strip()
        return snippet
    return " ".join(parts)


def _labels(items: object) -> list[str]:
    values: list[str] = []
    if not isinstance(items, list):
        return values
    for item in items:
        if not isinstance(item, dict):
            continue
        value = str(item.get("label", "")).strip()
        if value and value not in values:
            values.append(value)
    return values


def _join_labels(values: list[str]) -> str:
    return "; ".join(values)


def _min_confidence(items: list[object]) -> object:
    values = [
        float(item["confidence"])
        for item in items
        if isinstance(item, dict) and isinstance(item.get("confidence"), int | float)
    ]
    return min(values) if values else None
