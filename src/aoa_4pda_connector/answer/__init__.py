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
            "renderer": "starter_graph_context_v2",
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
