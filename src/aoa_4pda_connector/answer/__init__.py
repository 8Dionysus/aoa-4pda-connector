"""Answer rendering over local evidence packets."""

from __future__ import annotations


DEVICE_ANCHOR_TERMS = {
    "10",
    "13t",
    "2306epn60g",
    "2306epn60r",
    "aristotle",
    "note",
    "pro",
    "redmi",
    "sweet",
    "xiaomi",
    "xig04",
}
WEAK_QUERY_TERMS = {
    "about",
    "help",
    "info",
    "question",
    "what",
    "where",
    "абсолютно",
    "вообще",
    "вопрос",
    "инфа",
    "информация",
    "какая",
    "какой",
    "какую",
    "кто",
    "несуществующий",
    "полностью",
    "почему",
    "совершенно",
    "такой",
    "такая",
    "что",
}


def render_answer_packet(evidence_packet: dict[str, object], limit: int = 5) -> dict[str, object]:
    """Render a compact answer packet from a graph-enriched evidence packet."""

    policy = evidence_packet.get("policy", {})
    internal_search_used = bool(policy.get("internal_search_used")) if isinstance(policy, dict) else False
    packet_created_at = evidence_packet.get("created_at")
    evidence_results = [
        result
        for result in evidence_packet.get("results", [])[:limit]
        if isinstance(result, dict)
    ]
    grounding = _grounding_report(evidence_packet, evidence_results)
    answers = [
        _answer_for_result(result, packet_created_at=packet_created_at)
        for result in evidence_results
        if grounding["answer_status"] == "answered"
    ]
    return {
        "schema": "aoa_4pda_answer_packet_v1",
        "answer_id": str(evidence_packet.get("packet_id", "query")).replace("query-", "answer-", 1),
        "query": evidence_packet.get("query", ""),
        "created_at": packet_created_at,
        "answer_report": {
            "renderer": "starter_graph_context_v2",
            "source_packet_id": evidence_packet.get("packet_id"),
            "source_packet_schema": evidence_packet.get("schema"),
            "query_algorithm": evidence_packet.get("query_report", {}).get("algorithm")
            if isinstance(evidence_packet.get("query_report"), dict)
            else None,
            "graph_context_required": True,
            "freshness_context": "source_post_and_capture_metadata",
            **grounding,
        },
        "answers": answers,
        "policy": {
            "source": "local_keyword_index_plus_graph_answer_renderer",
            "internal_search_used": internal_search_used,
        },
    }


def _grounding_report(evidence_packet: dict[str, object], results: list[dict[str, object]]) -> dict[str, object]:
    query_report = evidence_packet.get("query_report", {})
    if not isinstance(query_report, dict):
        query_report = {}
    top_result = results[0] if results else {}
    metrics = _grounding_metrics(query_report, top_result)
    answered = _is_grounded(metrics)
    gap_reason = None if answered else _gap_reason(results, metrics)
    return {
        "answer_status": "answered" if answered else "insufficient_evidence",
        "gap_reason": gap_reason,
        "missing_evidence_note": None if answered else _missing_evidence_note(gap_reason),
        "candidate_result_count": len(results),
        "top_evidence_grounding": metrics,
    }


def _grounding_metrics(query_report: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    content_terms = _content_query_terms(query_report)
    matched_values = _matched_values(result)
    matched_content_terms = sorted(content_terms.intersection(matched_values))
    unmatched_structured_terms = sorted(_required_structured_terms(query_report).difference(matched_values))
    relation_supported = _relation_supported(result)
    content_phrase_supported = _content_phrase_supported(result, content_terms)
    return {
        "content_terms": sorted(content_terms),
        "matched_content_terms": matched_content_terms,
        "matched_content_term_count": len(matched_content_terms),
        "unmatched_structured_terms": unmatched_structured_terms,
        "relation_supported": relation_supported,
        "content_phrase_supported": content_phrase_supported,
    }


def _is_grounded(metrics: dict[str, object]) -> bool:
    if bool(metrics.get("relation_supported")):
        return True
    matched_count = int(metrics.get("matched_content_term_count") or 0)
    unmatched_structured = metrics.get("unmatched_structured_terms", [])
    has_unmatched_structured = bool(unmatched_structured) if isinstance(unmatched_structured, list) else False
    if has_unmatched_structured:
        return matched_count >= 3
    if matched_count >= 2:
        return True
    return matched_count >= 1 and bool(metrics.get("content_phrase_supported"))


def _gap_reason(results: list[dict[str, object]], metrics: dict[str, object]) -> str:
    if not results:
        return "no_candidate_evidence"
    if metrics.get("unmatched_structured_terms"):
        return "unmatched_structured_query_terms"
    return "candidate_evidence_below_grounding_threshold"


def _missing_evidence_note(gap_reason: object) -> str:
    reason = str(gap_reason or "candidate_evidence_below_grounding_threshold")
    return (
        "В базе недостаточно данных для надежного ответа. "
        f"Причина: {reason}; проверьте coverage/refresh или расширьте локальный корпус."
    )


def _content_query_terms(query_report: dict[str, object]) -> set[str]:
    values: set[str] = set()
    for field in ["terms", "exact_terms", "specific_terms", "technical_terms"]:
        for value in _strings(query_report.get(field, [])):
            normalized = _normalize_term(value)
            if _is_content_term(normalized):
                values.add(normalized)
    return values


def _required_structured_terms(query_report: dict[str, object]) -> set[str]:
    values: set[str] = set()
    for value in _strings(query_report.get("exact_terms", [])):
        normalized = _normalize_term(value)
        if _is_content_term(normalized) and _is_structured_term(normalized):
            values.add(normalized)
    return values


def _matched_values(result: dict[str, object]) -> set[str]:
    values: set[str] = set()
    for field in ["matched_terms", "matched_exact_terms", "matched_specific_terms"]:
        values.update(_normalize_term(value) for value in _strings(result.get(field, [])))
    for phrase in _strings(result.get("matched_phrases", [])):
        values.update(_normalize_term(value) for value in phrase.split())
        normalized_phrase = _normalize_term(phrase)
        if normalized_phrase:
            values.add(normalized_phrase)
    return {value for value in values if value}


def _relation_supported(result: dict[str, object]) -> bool:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        return False
    relation_edges = context.get("relation_edges", [])
    if isinstance(relation_edges, list) and any(isinstance(edge, dict) for edge in relation_edges):
        return True
    for field in ["fixes", "warnings"]:
        values = context.get(field, [])
        if isinstance(values, list) and values:
            return True
    rerank = result.get("relation_rerank", {})
    return isinstance(rerank, dict) and int(rerank.get("matching_edge_count") or 0) > 0


def _content_phrase_supported(result: dict[str, object], content_terms: set[str]) -> bool:
    for phrase in _strings(result.get("matched_phrases", [])):
        phrase_terms = {_normalize_term(value) for value in phrase.split()}
        if phrase_terms.intersection(content_terms):
            return True
    return False


def _is_content_term(value: str) -> bool:
    if len(value) < 3:
        return False
    return value not in DEVICE_ANCHOR_TERMS and value not in WEAK_QUERY_TERMS


def _is_structured_term(value: str) -> bool:
    return any(char.isdigit() for char in value) and any(char.isalpha() for char in value)


def _normalize_term(value: object) -> str:
    return str(value or "").strip().casefold()


def _strings(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item).strip() for item in items if str(item).strip()]


def _answer_for_result(result: dict[str, object], *, packet_created_at: object) -> dict[str, object]:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        context = {}
    issue_labels = _labels(context.get("issues", []))
    fix_labels = _labels(context.get("fixes", []))
    warning_labels = _labels(context.get("warnings", []))
    warned_target_labels = _labels(context.get("warned_targets", []))
    relation_edges = context.get("relation_edges", [])
    if not isinstance(relation_edges, list):
        relation_edges = []
    entity_node_ids = context.get("entity_node_ids", [])
    if not isinstance(entity_node_ids, list):
        entity_node_ids = []
    relation_labels = _relation_labels(relation_edges, entity_node_ids)
    root_action_labels = relation_labels["root_action_labels"]
    recovery_action_labels = relation_labels["recovery_action_labels"]
    target_file_labels = relation_labels["target_file_labels"]
    tool_labels = relation_labels["tool_labels"]
    firmware_context_labels = relation_labels["firmware_context_labels"]
    answer_kind = _answer_kind(
        issue_labels,
        fix_labels,
        warning_labels,
        root_action_labels,
        recovery_action_labels,
    )

    return {
        "answer_kind": answer_kind,
        "answer_text": _answer_text(
            result,
            issue_labels,
            fix_labels,
            warning_labels,
            warned_target_labels,
            root_action_labels,
            recovery_action_labels,
            target_file_labels,
            tool_labels,
            firmware_context_labels,
        ),
        "source_url": result.get("source_url"),
        "topic_id": result.get("topic_id"),
        "post_id": result.get("post_id"),
        "posted_at": result.get("posted_at"),
        "captured_at": result.get("captured_at"),
        "chunk_id": result.get("chunk_id"),
        "score": result.get("score"),
        "score_breakdown": result.get("score_breakdown", {}),
        "issue_labels": issue_labels,
        "fix_labels": fix_labels,
        "warning_labels": warning_labels,
        "warned_target_labels": warned_target_labels,
        "root_action_labels": root_action_labels,
        "recovery_action_labels": recovery_action_labels,
        "target_file_labels": target_file_labels,
        "tool_labels": tool_labels,
        "firmware_context_labels": firmware_context_labels,
        "evidence_refs": result.get("evidence_refs", []),
        "source_refs": context.get("source_refs", []) or ([result.get("source_url")] if result.get("source_url") else []),
        "freshness": _freshness(result, packet_created_at=packet_created_at),
        "confidence": {
            "basis": "starter_graph_context" if context else "keyword_result",
            "relation_confidence_min": _min_confidence(relation_edges),
            "result_score": result.get("score"),
        },
    }


def _answer_kind(
    issue_labels: list[str],
    fix_labels: list[str],
    warning_labels: list[str],
    root_action_labels: list[str],
    recovery_action_labels: list[str],
) -> str:
    if issue_labels and fix_labels and warning_labels:
        return "issue_fix_warning"
    if issue_labels and fix_labels:
        return "issue_fix"
    if warning_labels:
        return "warning"
    if root_action_labels and recovery_action_labels:
        return "root_recovery"
    if root_action_labels:
        return "root"
    if recovery_action_labels:
        return "recovery"
    return "snippet"


def _answer_text(
    result: dict[str, object],
    issue_labels: list[str],
    fix_labels: list[str],
    warning_labels: list[str],
    warned_target_labels: list[str],
    root_action_labels: list[str],
    recovery_action_labels: list[str],
    target_file_labels: list[str],
    tool_labels: list[str],
    firmware_context_labels: list[str],
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
    if root_action_labels:
        parts.append(f"Root actions: {_join_labels(root_action_labels)}.")
    if recovery_action_labels:
        parts.append(f"Recovery actions: {_join_labels(recovery_action_labels)}.")
    if target_file_labels:
        parts.append(f"Target files: {_join_labels(target_file_labels)}.")
    if tool_labels:
        parts.append(f"Tools: {_join_labels(tool_labels)}.")
    if firmware_context_labels:
        parts.append(f"Firmware context: {_join_labels(firmware_context_labels)}.")
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


def _relation_labels(relation_edges: list[object], entity_node_ids: list[object]) -> dict[str, list[str]]:
    labels = {
        "root_action_labels": [],
        "recovery_action_labels": [],
        "target_file_labels": [],
        "tool_labels": [],
        "firmware_context_labels": [],
    }
    for node_id in entity_node_ids:
        kind, label = _entity_node_parts(node_id)
        if kind == "root_action":
            _append_unique(labels["root_action_labels"], label)
        elif kind == "recovery_action":
            _append_unique(labels["recovery_action_labels"], label)

    for edge in relation_edges:
        if not isinstance(edge, dict):
            continue
        edge_kind = str(edge.get("kind", ""))
        from_kind, from_label = _entity_node_parts(edge.get("from_node"))
        to_kind, to_label = _entity_node_parts(edge.get("to_node"))
        if edge_kind.startswith("root_") and from_kind == "root_action":
            _append_unique(labels["root_action_labels"], from_label)
        elif edge_kind.startswith("recovery_") and from_kind == "recovery_action":
            _append_unique(labels["recovery_action_labels"], from_label)

        if edge_kind.endswith("_targets_file") and to_kind == "file":
            _append_unique(labels["target_file_labels"], to_label)
        elif edge_kind.endswith("_uses_tool") and to_kind == "tool":
            _append_unique(labels["tool_labels"], to_label)
        elif edge_kind.endswith("_mentions_firmware") and to_kind in {
            "build_id",
            "firmware_family",
            "firmware_version",
        }:
            _append_unique(labels["firmware_context_labels"], to_label)
    return labels


def _entity_node_parts(node_id: object) -> tuple[str, str]:
    text = str(node_id or "")
    if not text.startswith("entity:"):
        return "", text
    parts = text.split(":", 2)
    if len(parts) != 3:
        return "", text
    return parts[1], parts[2]


def _append_unique(values: list[str], value: str) -> None:
    normalized = value.strip()
    if normalized and normalized not in values:
        values.append(normalized)


def _min_confidence(items: list[object]) -> object:
    values = [
        float(item["confidence"])
        for item in items
        if isinstance(item, dict) and isinstance(item.get("confidence"), int | float)
    ]
    return min(values) if values else None


def _freshness(result: dict[str, object], *, packet_created_at: object) -> dict[str, object]:
    posted_at = _non_empty(result.get("posted_at"))
    captured_at = _non_empty(result.get("captured_at"))
    packet_time = _non_empty(packet_created_at)
    basis = "source_post_and_capture_metadata" if captured_at else "packet_created_at_fallback"
    if posted_at and captured_at:
        note = "Public post timestamp and local capture timestamp are available for this evidence."
    elif captured_at:
        note = "Local capture timestamp is available; public post timestamp was not parsed for this evidence."
    else:
        note = "Source capture timestamp is not present in this index; packet creation time is retained as fallback context."
    return {
        "basis": basis,
        "posted_at": posted_at,
        "captured_at": captured_at,
        "packet_created_at": packet_time,
        "note": note,
    }


def _non_empty(value: object) -> object:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
