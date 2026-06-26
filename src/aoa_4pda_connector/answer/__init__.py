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
WARNING_QUERY_TERMS = {
    "danger",
    "dangerous",
    "risk",
    "warn",
    "warning",
    "опасно",
    "осторожно",
    "предупреждение",
    "предупреждения",
    "риск",
    "риски",
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
    query_report = _query_report(evidence_packet)
    grounding_entries = _grounding_entries(query_report, evidence_results)
    grounded_entries = [entry for entry in grounding_entries if entry["grounded"] is True]
    answer_entries, deduplicated_count = _dedupe_grounded_entries(grounded_entries)
    grounding = _grounding_report(evidence_results, grounding_entries, answer_entries, deduplicated_count)
    answers = [
        _answer_for_result(entry["result"], packet_created_at=packet_created_at)
        for entry in answer_entries
    ]
    evidence_chain = _evidence_chain(answers, answer_entries)
    nuance_report = _nuance_report(evidence_chain, grounding)
    conflict_report = _conflict_report(evidence_chain, grounding)
    freshness_report = _freshness_report(evidence_chain, nuance_report, conflict_report)
    applicability_report = _applicability_report(evidence_packet.get("query", ""), evidence_chain, grounding)
    warning_report = _warning_report(evidence_chain, query_report)
    return {
        "schema": "aoa_4pda_answer_packet_v1",
        "answer_id": str(evidence_packet.get("packet_id", "query")).replace("query-", "answer-", 1),
        "query": evidence_packet.get("query", ""),
        "created_at": packet_created_at,
        "answer_report": {
            "renderer": "starter_graph_context_v2",
            "source_packet_id": evidence_packet.get("packet_id"),
            "source_packet_schema": evidence_packet.get("schema"),
            "query_algorithm": query_report.get("algorithm"),
            "graph_context_required": True,
            "freshness_context": "source_post_and_capture_metadata",
            **grounding,
        },
        "answers": answers,
        "evidence_chain": evidence_chain,
        "nuance_report": nuance_report,
        "conflict_report": conflict_report,
        "freshness_report": freshness_report,
        "applicability_report": applicability_report,
        "warning_report": warning_report,
        "agent_answer": _agent_answer(
            evidence_packet.get("query", ""),
            evidence_chain,
            nuance_report,
            grounding,
            conflict_report,
            freshness_report,
            warning_report,
        ),
        "policy": {
            "source": "local_keyword_index_plus_graph_answer_renderer",
            "internal_search_used": internal_search_used,
        },
        "network_touched": False,
        "read_only": True,
    }


def _query_report(evidence_packet: dict[str, object]) -> dict[str, object]:
    query_report = evidence_packet.get("query_report", {})
    if not isinstance(query_report, dict):
        return {}
    return query_report


def _grounding_entries(query_report: dict[str, object], results: list[dict[str, object]]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for result in results:
        metrics = _grounding_metrics(query_report, result)
        entries.append(
            {
                "result": result,
                "grounding": metrics,
                "grounded": _is_grounded(metrics),
            }
        )
    return entries


def _dedupe_grounded_entries(entries: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
    seen: set[str] = set()
    deduped: list[dict[str, object]] = []
    duplicate_count = 0
    for entry in entries:
        result = entry.get("result", {})
        key = _dedupe_key(result) if isinstance(result, dict) else ""
        if key and key in seen:
            duplicate_count += 1
            continue
        if key:
            seen.add(key)
        deduped.append(entry)
    return deduped, duplicate_count


def _dedupe_key(result: dict[str, object]) -> str:
    post_id = _non_empty(result.get("post_id"))
    if post_id:
        return f"post:{post_id}"
    source_url = _non_empty(result.get("source_url"))
    if source_url:
        return f"url:{source_url}"
    chunk_id = _non_empty(result.get("chunk_id"))
    return f"chunk:{chunk_id}" if chunk_id else ""


def _grounding_report(
    results: list[dict[str, object]],
    entries: list[dict[str, object]],
    answer_entries: list[dict[str, object]],
    deduplicated_count: int,
) -> dict[str, object]:
    top_metrics = entries[0]["grounding"] if entries else _grounding_metrics({}, {})
    primary_metrics = answer_entries[0]["grounding"] if answer_entries else None
    grounded_count = sum(1 for entry in entries if entry.get("grounded") is True)
    filtered_count = max(0, len(results) - grounded_count)
    answered = bool(answer_entries)
    gap_reason = None if answered else _gap_reason(results, top_metrics)
    return {
        "answer_status": "answered" if answered else "insufficient_evidence",
        "gap_reason": gap_reason,
        "missing_evidence_note": None if answered else _missing_evidence_note(gap_reason),
        "candidate_result_count": len(results),
        "grounded_candidate_count": grounded_count,
        "filtered_candidate_count": filtered_count,
        "deduplicated_candidate_count": deduplicated_count,
        "top_evidence_grounding": top_metrics,
        "primary_evidence_grounding": primary_metrics,
    }


def _evidence_chain(answers: list[dict[str, object]], entries: list[dict[str, object]]) -> list[dict[str, object]]:
    chain: list[dict[str, object]] = []
    for index, (answer, entry) in enumerate(zip(answers, entries, strict=True), start=1):
        result = entry.get("result", {})
        grounding = entry.get("grounding", {})
        if not isinstance(result, dict):
            result = {}
        if not isinstance(grounding, dict):
            grounding = {}
        relation_kinds = _relation_kinds_for_result(result)
        claim_relation_edges = _claim_relation_edges_for_result(result)
        claim_ids = _claim_ids_for_result(result)
        freshness = answer.get("freshness", {})
        chain.append(
            {
                "chain_step": index,
                "role": _chain_role(index, answer, relation_kinds),
                "answer_kind": answer.get("answer_kind"),
                "summary": answer.get("answer_text"),
                "source_url": answer.get("source_url"),
                "topic_id": answer.get("topic_id"),
                "post_id": answer.get("post_id"),
                "chunk_id": answer.get("chunk_id"),
                "posted_at": answer.get("posted_at"),
                "captured_at": answer.get("captured_at"),
                "freshness": freshness if isinstance(freshness, dict) else {},
                "evidence_refs": answer.get("evidence_refs", []),
                "source_refs": answer.get("source_refs", []),
                "claim_ids": claim_ids,
                "claim_relation_edges": claim_relation_edges,
                "claim_freshness_windows": answer.get("claim_freshness_windows", []),
                "matched_terms": _strings(result.get("matched_terms", [])),
                "matched_exact_terms": _strings(result.get("matched_exact_terms", [])),
                "matched_specific_terms": _strings(result.get("matched_specific_terms", [])),
                "matched_content_terms": _strings(grounding.get("matched_content_terms", [])),
                "relation_kinds": relation_kinds,
                "issue_labels": answer.get("issue_labels", []),
                "fix_labels": answer.get("fix_labels", []),
                "warning_labels": answer.get("warning_labels", []),
                "warned_target_labels": answer.get("warned_target_labels", []),
                "root_action_labels": answer.get("root_action_labels", []),
                "recovery_action_labels": answer.get("recovery_action_labels", []),
                "target_file_labels": answer.get("target_file_labels", []),
                "tool_labels": answer.get("tool_labels", []),
                "firmware_context_labels": answer.get("firmware_context_labels", []),
                "claim_context_labels": answer.get("claim_context_labels", []),
                "claim_condition_labels": answer.get("claim_condition_labels", []),
                "score": answer.get("score"),
            }
        )
    return chain


def _chain_role(index: int, answer: dict[str, object], relation_kinds: list[str]) -> str:
    if index == 1:
        return "primary"
    if "claim_contradicts_claim" in relation_kinds or "claim_deprecated_for_context" in relation_kinds:
        return "conflicting"
    if "claim_supersedes_claim" in relation_kinds:
        return "superseding"
    if "claim_contextualizes_claim" in relation_kinds:
        return "contextual"
    if answer.get("warning_labels"):
        return "caution"
    if relation_kinds:
        return "supporting"
    return "related_context"


def _nuance_report(chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    limitations: list[dict[str, object]] = []
    filtered_count = int(grounding.get("filtered_candidate_count") or 0)
    deduplicated_count = int(grounding.get("deduplicated_candidate_count") or 0)
    if filtered_count:
        limitations.append({"kind": "filtered_weak_candidates", "count": filtered_count})
    if deduplicated_count:
        limitations.append({"kind": "deduplicated_same_post_chunks", "count": deduplicated_count})
    if not chain and grounding.get("answer_status") == "insufficient_evidence":
        limitations.append({"kind": str(grounding.get("gap_reason") or "insufficient_evidence"), "count": 1})

    return {
        "chain_step_count": len(chain),
        "topic_count": len({step.get("topic_id") for step in chain if step.get("topic_id")}),
        "post_count": len({step.get("post_id") for step in chain if step.get("post_id")}),
        "source_count": len({step.get("source_url") for step in chain if step.get("source_url")}),
        "answer_kinds": _unique_sorted(step.get("answer_kind") for step in chain),
        "relation_kinds": _unique_sorted(
            relation_kind
            for step in chain
            for relation_kind in step.get("relation_kinds", [])
            if isinstance(step.get("relation_kinds"), list)
        ),
        "matched_content_terms": _unique_sorted(
            term
            for step in chain
            for term in step.get("matched_content_terms", [])
            if isinstance(step.get("matched_content_terms"), list)
        ),
        "freshness": _chain_freshness(chain),
        "limitations": limitations,
    }


def _chain_freshness(chain: list[dict[str, object]]) -> dict[str, object]:
    captured_at_values = _unique_sorted(step.get("captured_at") for step in chain)
    posted_at_values = _unique_sorted(step.get("posted_at") for step in chain)
    return {
        "basis": "source_post_and_capture_metadata" if captured_at_values else "no_answer_evidence",
        "latest_captured_at": max(captured_at_values) if captured_at_values else None,
        "captured_at_values": captured_at_values,
        "posted_at_values": posted_at_values,
    }


def _conflict_report(chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    if not chain or grounding.get("answer_status") == "insufficient_evidence":
        return {
            "schema": "aoa_connector_conflict_report_v1",
            "status": "insufficient_evidence",
            "primary_claim_id": None,
            "primary_post_id": None,
            "supporting_claim_ids": [],
            "conflicting_claim_ids": [],
            "superseding_claim_ids": [],
            "contextual_claim_ids": [],
            "warnings": [],
            "missing": _missing_gap_categories(grounding),
            "confidence": "none",
            "primary_selection_reason": "No grounded evidence chain was available.",
            "demotion_reasons": [],
        }

    edges = _chain_claim_relation_edges(chain)
    primary = chain[0]
    primary_claims = _strings(primary.get("claim_ids", []))
    supporting_claims = _claim_ids_by_role(chain, {"supporting", "caution", "contextual"})
    conflicting_claims = _edge_claim_ids(edges, {"claim_contradicts_claim", "claim_deprecated_for_context"})
    superseding_claims = _edge_claim_ids(edges, {"claim_supersedes_claim"})
    contextual_claims = _edge_claim_ids(edges, {"claim_contextualizes_claim"})
    status = "clear"
    if conflicting_claims:
        status = "conflict_detected"
    elif superseding_claims:
        status = "possibly_superseded"
    elif contextual_claims:
        status = "contextualized"
    return {
        "schema": "aoa_connector_conflict_report_v1",
        "status": status,
        "primary_claim_id": primary_claims[0] if primary_claims else None,
        "primary_post_id": primary.get("post_id"),
        "supporting_claim_ids": supporting_claims,
        "conflicting_claim_ids": conflicting_claims,
        "superseding_claim_ids": superseding_claims,
        "contextual_claim_ids": contextual_claims,
        "warnings": _warning_claim_ids(chain),
        "missing": [],
        "confidence": _report_confidence(chain, conflicting_claims, superseding_claims),
        "primary_selection_reason": "Primary source is the top grounded local evidence result; conflict and freshness reports explain any demotion pressure.",
        "demotion_reasons": _demotion_reasons(edges),
    }


def _freshness_report(
    chain: list[dict[str, object]],
    nuance_report: dict[str, object],
    conflict_report: dict[str, object],
) -> dict[str, object]:
    freshness = nuance_report.get("freshness", {})
    if not isinstance(freshness, dict):
        freshness = {}
    windows = _unique_sorted(
        window
        for step in chain
        for window in step.get("claim_freshness_windows", [])
        if isinstance(step.get("claim_freshness_windows"), list)
    )
    if not chain:
        state = "not_enough_local_evidence"
    elif conflict_report.get("status") == "conflict_detected":
        state = "conflicting_evidence"
    elif conflict_report.get("status") == "possibly_superseded":
        state = "possibly_superseded"
    elif "latest_window" in windows:
        state = "fresh_answer"
    elif conflict_report.get("status") == "contextualized":
        state = "old_with_newer_context"
    else:
        state = "old_but_still_supported"
    return {
        "schema": "aoa_connector_freshness_report_v1",
        "state": state,
        "basis": freshness.get("basis") or "source_post_and_capture_metadata",
        "latest_captured_at": freshness.get("latest_captured_at"),
        "captured_at_values": freshness.get("captured_at_values", []),
        "posted_at_values": freshness.get("posted_at_values", []),
        "profile_windows": windows,
        "newer_related_claims_visible": bool(conflict_report.get("superseding_claim_ids")),
        "local_base_stale_possible": state in {"possibly_superseded", "old_with_newer_context", "not_enough_local_evidence"},
    }


def _applicability_report(query: object, chain: list[dict[str, object]], grounding: dict[str, object]) -> dict[str, object]:
    contexts = _unique_sorted(
        label
        for step in chain
        for field in ["firmware_context_labels", "claim_context_labels"]
        for label in step.get(field, [])
        if isinstance(step.get(field), list)
    )
    conditions = _unique_sorted(
        label
        for step in chain
        for label in step.get("claim_condition_labels", [])
        if isinstance(step.get("claim_condition_labels"), list)
    )
    query_text = str(query or "").casefold()
    asks_current_context = any(term in query_text for term in ["now", "current", "сейчас", "актуаль", "можно ли"])
    missing_context = []
    if grounding.get("answer_status") == "insufficient_evidence":
        missing_context.append("source_coverage")
    if asks_current_context and not contexts:
        missing_context.append("version_or_region_or_state_context")
    return {
        "schema": "aoa_connector_applicability_report_v1",
        "status": "context_required" if missing_context else "context_available",
        "context_labels": contexts,
        "condition_labels": conditions,
        "missing_context": missing_context,
        "applicability_basis": "claim_context_and_firmware_entities",
    }


def _warning_report(chain: list[dict[str, object]], query_report: dict[str, object]) -> dict[str, object]:
    warning_labels = _unique_sorted(
        label
        for step in chain
        for label in step.get("warning_labels", [])
        if isinstance(step.get("warning_labels"), list)
    )
    warning_targets = _unique_sorted(
        label
        for step in chain
        for label in step.get("warned_target_labels", [])
        if isinstance(step.get("warned_target_labels"), list)
    )
    warning_edges = [
        edge
        for edge in _chain_claim_relation_edges(chain)
        if edge.get("kind") in {"source_warns_about_claim", "warning_targets_object", "warning_targets_action", "claim_contradicts_claim"}
    ]
    requested = _warning_requested(query_report)
    return {
        "schema": "aoa_connector_warning_report_v1",
        "warning_requested": requested,
        "warning_supported": bool(warning_labels or warning_edges),
        "risk_status": "warning_present" if warning_labels or warning_edges else "no_warning_claim_in_evidence",
        "warning_labels": warning_labels,
        "warning_target_labels": warning_targets,
        "warning_claim_ids": _warning_claim_ids(chain),
        "relation_count": len(warning_edges),
    }


def _missing_gap_categories(grounding: dict[str, object]) -> list[str]:
    reason = str(grounding.get("gap_reason") or "insufficient_evidence")
    if reason == "no_candidate_evidence":
        return ["source_coverage", "freshness", "conflict", "context", "warning"]
    if reason == "unmatched_structured_query_terms":
        return ["context", "source_coverage"]
    return ["source_coverage"]


def _chain_claim_relation_edges(chain: list[dict[str, object]]) -> list[dict[str, object]]:
    edges: list[dict[str, object]] = []
    seen: set[str] = set()
    for step in chain:
        relation_edges = step.get("claim_relation_edges", [])
        if not isinstance(relation_edges, list):
            continue
        for edge in relation_edges:
            if not isinstance(edge, dict):
                continue
            edge_id = str(edge.get("edge_id") or f"{edge.get('kind')}:{edge.get('from_node')}:{edge.get('to_node')}")
            if edge_id in seen:
                continue
            seen.add(edge_id)
            edges.append(edge)
    return edges


def _claim_ids_by_role(chain: list[dict[str, object]], roles: set[str]) -> list[str]:
    return _unique_sorted(
        claim_id
        for step in chain
        if step.get("role") in roles
        for claim_id in step.get("claim_ids", [])
        if isinstance(step.get("claim_ids"), list)
    )


def _edge_claim_ids(edges: list[dict[str, object]], kinds: set[str]) -> list[str]:
    values: list[str] = []
    for edge in edges:
        if edge.get("kind") not in kinds:
            continue
        for endpoint in [edge.get("from_node"), edge.get("to_node")]:
            text = str(endpoint or "")
            if text.startswith("claim:"):
                values.append(text)
    return _unique_sorted(values)


def _warning_claim_ids(chain: list[dict[str, object]]) -> list[str]:
    values: list[str] = []
    for step in chain:
        if step.get("warning_labels"):
            values.extend(_strings(step.get("claim_ids", [])))
    for edge in _chain_claim_relation_edges(chain):
        if edge.get("kind") == "source_warns_about_claim" and str(edge.get("to_node") or "").startswith("claim:"):
            values.append(str(edge.get("to_node")))
    return _unique_sorted(values)


def _report_confidence(
    chain: list[dict[str, object]],
    conflicting_claims: list[str],
    superseding_claims: list[str],
) -> str:
    if not chain:
        return "none"
    if conflicting_claims:
        return "bounded_conflict_visible"
    if superseding_claims:
        return "bounded_freshness_pressure_visible"
    if len(chain) >= 2:
        return "supported_by_multiple_local_sources"
    return "single_grounded_source"


def _demotion_reasons(edges: list[dict[str, object]]) -> list[dict[str, object]]:
    reasons: list[dict[str, object]] = []
    for edge in edges:
        kind = str(edge.get("kind") or "")
        if kind not in {"claim_contradicts_claim", "claim_supersedes_claim", "claim_deprecated_for_context", "claim_contextualizes_claim"}:
            continue
        reasons.append(
            {
                "kind": kind,
                "from_claim_id": edge.get("from_node"),
                "to_claim_id": edge.get("to_node"),
                "reason": edge.get("relation_reason"),
                "manual_review_required": edge.get("manual_review_required"),
            }
        )
    return reasons


def _agent_answer(
    query: object,
    chain: list[dict[str, object]],
    nuance_report: dict[str, object],
    grounding: dict[str, object],
    conflict_report: dict[str, object],
    freshness_report: dict[str, object],
    warning_report: dict[str, object],
) -> dict[str, object]:
    status = str(grounding.get("answer_status") or "insufficient_evidence")
    citations = _agent_citations(chain)
    freshness = nuance_report.get("freshness", {})
    if not isinstance(freshness, dict):
        freshness = {}
    limitations = nuance_report.get("limitations", [])
    if not isinstance(limitations, list):
        limitations = []

    if status != "answered" or not chain:
        text = _non_empty(grounding.get("missing_evidence_note")) or _missing_evidence_note(
            grounding.get("gap_reason")
        )
        return {
            "format": "deterministic_cited_brief_v1",
            "status": "insufficient_evidence",
            "language": "ru",
            "query": str(query or ""),
            "text": text,
            "citations": [],
            "freshness": freshness,
            "limitations": limitations,
            "conflict_status": conflict_report.get("status"),
            "freshness_state": freshness_report.get("state"),
            "warning_status": warning_report.get("risk_status"),
        }

    text_parts = []
    primary = chain[0]
    text_parts.append(f"По локальной базе 4PDA: {_brief_sentence(primary.get('summary'))} [1].")
    additional_context = _additional_context_brief(chain[1:])
    if additional_context:
        text_parts.append(additional_context)
    freshness_text = _freshness_brief(freshness)
    if freshness_text:
        text_parts.append(freshness_text)
    limitation_text = _limitations_brief(limitations)
    if limitation_text:
        text_parts.append(limitation_text)
    conflict_text = _conflict_brief(conflict_report, warning_report)
    if conflict_text:
        text_parts.append(conflict_text)

    return {
        "format": "deterministic_cited_brief_v1",
        "status": "answered",
        "language": "ru",
        "query": str(query or ""),
        "text": " ".join(text_parts),
        "citations": citations,
        "freshness": freshness,
        "limitations": limitations,
        "conflict_status": conflict_report.get("status"),
        "freshness_state": freshness_report.get("state"),
        "warning_status": warning_report.get("risk_status"),
    }


def _agent_citations(chain: list[dict[str, object]]) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    for index, step in enumerate(chain, start=1):
        citations.append(
            {
                "ref": f"[{index}]",
                "role": step.get("role"),
                "topic_id": step.get("topic_id"),
                "post_id": step.get("post_id"),
                "chunk_id": step.get("chunk_id"),
                "source_url": step.get("source_url"),
                "posted_at": step.get("posted_at"),
                "captured_at": step.get("captured_at"),
                "evidence_refs": step.get("evidence_refs", []),
                "claim_ids": step.get("claim_ids", []),
            }
        )
    return citations


def _sentence_text(value: object) -> str:
    text = str(value or "").strip()
    return text[:-1] if text.endswith(".") else text


def _brief_sentence(value: object, max_chars: int = 260) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].rstrip(".,;: ") + "..."
    return _sentence_text(text)


def _additional_context_brief(steps: list[dict[str, object]]) -> str:
    if not steps:
        return ""
    refs = [f"[{index}]" for index in range(2, len(steps) + 2)]
    matched_terms = _unique_sorted(
        term
        for step in steps
        for term in step.get("matched_content_terms", [])
        if isinstance(step.get("matched_content_terms"), list)
    )
    relation_kinds = _unique_sorted(
        relation_kind
        for step in steps
        for relation_kind in step.get("relation_kinds", [])
        if isinstance(step.get("relation_kinds"), list)
    )
    details = []
    if matched_terms:
        details.append(f"matched terms: {', '.join(matched_terms)}")
    if relation_kinds:
        details.append(f"relation kinds: {', '.join(relation_kinds)}")
    suffix = f" ({'; '.join(details)})" if details else ""
    return f"Дополнительный контекст: см. {', '.join(refs)}{suffix}."


def _freshness_brief(freshness: dict[str, object]) -> str:
    latest = _non_empty(freshness.get("latest_captured_at"))
    if latest:
        return f"Свежесть: последнее локальное сохранение источников {latest}."
    basis = _non_empty(freshness.get("basis"))
    if basis == "no_answer_evidence":
        return "Свежесть: в пакете нет подтвержденной ответной цепочки."
    return ""


def _limitations_brief(limitations: list[object]) -> str:
    parts: list[str] = []
    labels = {
        "filtered_weak_candidates": "отфильтровано слабых кандидатов",
        "deduplicated_same_post_chunks": "схлопнуто дублей постов",
        "no_candidate_evidence": "нет кандидатной выдачи",
        "unmatched_structured_query_terms": "не совпали структурные термины запроса",
        "candidate_evidence_below_grounding_threshold": "кандидаты ниже порога grounding",
        "insufficient_evidence": "недостаточно подтвержденной evidence",
    }
    for limitation in limitations:
        if not isinstance(limitation, dict):
            continue
        kind = str(limitation.get("kind") or "").strip()
        count = limitation.get("count")
        if not kind or count is None:
            continue
        label = labels.get(kind, kind)
        parts.append(f"{label}: {count}")
    return f"Ограничения: {'; '.join(parts)}." if parts else ""


def _conflict_brief(conflict_report: dict[str, object], warning_report: dict[str, object]) -> str:
    parts: list[str] = []
    status = str(conflict_report.get("status") or "")
    if status in {"conflict_detected", "possibly_superseded", "contextualized"}:
        parts.append(f"Семантика claims: {status}.")
    if warning_report.get("warning_supported"):
        parts.append("Предупреждения/риски присутствуют в evidence.")
    return " ".join(parts)


def _relation_kinds_for_result(result: dict[str, object]) -> list[str]:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        return []
    relation_edges = context.get("relation_edges", [])
    if not isinstance(relation_edges, list):
        return []
    return _unique_sorted(
        edge.get("kind")
        for edge in relation_edges
        if isinstance(edge, dict)
    )


def _claim_relation_edges_for_result(result: dict[str, object]) -> list[dict[str, object]]:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        return []
    relation_edges = context.get("relation_edges", [])
    if not isinstance(relation_edges, list):
        return []
    return [
        edge
        for edge in relation_edges
        if isinstance(edge, dict)
        and str(edge.get("kind") or "").startswith(("claim_", "source_", "method_", "warning_"))
    ]


def _claim_ids_for_result(result: dict[str, object]) -> list[str]:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        return []
    return _strings(context.get("claim_node_ids", []))


def _unique_sorted(values: object) -> list[str]:
    unique = {str(value).strip() for value in values if str(value or "").strip()}
    return sorted(unique)


def _grounding_metrics(query_report: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    content_terms = _content_query_terms(query_report)
    matched_values = _matched_values(result)
    matched_content_terms = sorted(content_terms.intersection(matched_values))
    unmatched_structured_terms = sorted(_required_structured_terms(query_report).difference(matched_values))
    relation_supported = _relation_supported(result)
    content_phrase_supported = _content_phrase_supported(result, content_terms)
    warning_requested = _warning_requested(query_report)
    warning_supported = _warning_supported(result)
    return {
        "content_terms": sorted(content_terms),
        "matched_content_terms": matched_content_terms,
        "matched_content_term_count": len(matched_content_terms),
        "unmatched_structured_terms": unmatched_structured_terms,
        "relation_supported": relation_supported,
        "content_phrase_supported": content_phrase_supported,
        "warning_requested": warning_requested,
        "warning_supported": warning_supported,
    }


def _is_grounded(metrics: dict[str, object]) -> bool:
    if bool(metrics.get("warning_requested")) and not bool(metrics.get("warning_supported")):
        return False
    if bool(metrics.get("relation_supported")):
        return True
    matched_count = int(metrics.get("matched_content_term_count") or 0)
    content_terms = metrics.get("content_terms", [])
    content_term_count = len(content_terms) if isinstance(content_terms, list) else 0
    unmatched_structured = metrics.get("unmatched_structured_terms", [])
    has_unmatched_structured = bool(unmatched_structured) if isinstance(unmatched_structured, list) else False
    if has_unmatched_structured:
        return matched_count >= 3
    if content_term_count >= 5:
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
    rerank = result.get("relation_rerank", {})
    if isinstance(rerank, dict):
        intents = rerank.get("intents", [])
        if isinstance(intents, list):
            if intents:
                return int(rerank.get("matching_edge_count") or 0) > 0
            for field in ["fixes", "warnings"]:
                values = context.get(field, [])
                if isinstance(values, list) and values:
                    return True
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


def _warning_requested(query_report: dict[str, object]) -> bool:
    terms = {
        _normalize_term(value)
        for field in ["terms", "exact_terms", "specific_terms", "technical_terms"]
        for value in _strings(query_report.get(field, []))
    }
    return bool(terms.intersection(WARNING_QUERY_TERMS))


def _warning_supported(result: dict[str, object]) -> bool:
    context = result.get("graph_context", {})
    if not isinstance(context, dict):
        return False
    for field in ["warnings", "warned_targets"]:
        values = context.get(field, [])
        if isinstance(values, list) and values:
            return True
    relation_edges = context.get("relation_edges", [])
    return isinstance(relation_edges, list) and any(
        isinstance(edge, dict)
        and edge.get("kind")
        in {"warns_about", "source_warns_about_claim", "warning_targets_object", "warning_targets_action", "claim_contradicts_claim"}
        for edge in relation_edges
    )


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
    claims = context.get("claims", [])
    if not isinstance(claims, list):
        claims = []
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
    claim_ids = _strings(context.get("claim_node_ids", []))
    claim_context_labels = _claim_field_labels(claims, "applicability_context")
    claim_condition_labels = _claim_field_labels(claims, "condition_labels")
    claim_freshness_windows = _claim_freshness_windows(claims)
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
        "claim_ids": claim_ids,
        "claim_context_labels": claim_context_labels,
        "claim_condition_labels": claim_condition_labels,
        "claim_freshness_windows": claim_freshness_windows,
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


def _claim_field_labels(claims: list[object], field: str) -> list[str]:
    labels: list[str] = []
    for item in claims:
        if not isinstance(item, dict):
            continue
        claim = item.get("claim", {})
        if not isinstance(claim, dict):
            continue
        for value in _strings(claim.get(field, [])):
            _append_unique(labels, value)
    return labels


def _claim_freshness_windows(claims: list[object]) -> list[str]:
    windows: list[str] = []
    for item in claims:
        if not isinstance(item, dict):
            continue
        claim = item.get("claim", {})
        if not isinstance(claim, dict):
            continue
        freshness = claim.get("freshness_context", {})
        if isinstance(freshness, dict):
            _append_unique(windows, str(freshness.get("profile_window") or ""))
    return windows


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
