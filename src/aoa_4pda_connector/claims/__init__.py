"""Portable claim extraction primitives for forum evidence graphs."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime


CLAIM_EXTRACTOR_VERSION = "claim_heuristic_v1"
RELATION_EXTRACTOR_VERSION = "claim_relation_heuristic_v1"
CLAIM_RELATION_KINDS = {
    "claim_applies_to_context",
    "method_uses_tool",
    "method_targets_object",
    "method_requires_condition",
    "warning_targets_action",
    "warning_targets_object",
    "claim_contextualizes_claim",
    "claim_supersedes_claim",
    "claim_contradicts_claim",
    "claim_deprecated_for_context",
    "source_supports_claim",
    "source_warns_about_claim",
    "source_updates_claim",
    "claim_confirms_claim",
    "claim_refines_claim",
    "claim_scope_limited_by",
    "claim_unknown_for_context",
    "claim_requires_manual_review",
}

ROOT_METHOD_TOOLS = {"KSU", "Magisk"}
RECOVERY_METHOD_TOOLS = {"OrangeFox", "TWRP", "fastboot"}
WARNING_TERMS = (
    "danger",
    "do not",
    "don't",
    "not safe",
    "risk",
    "warning",
    "важно",
    "кирпич",
    "нельзя",
    "не ставить",
    "не шить",
    "не прошивать",
    "опасно",
    "осторожно",
    "риск",
)
UPDATE_TERMS = (
    "after update",
    "current",
    "latest",
    "new build",
    "no longer",
    "now",
    "since update",
    "works now",
    "актуально",
    "новая",
    "новой",
    "обновления",
    "после обнов",
    "сейчас",
    "теперь",
)
NEGATIVE_STATUS_TERMS = (
    "no longer",
    "not work",
    "doesn't work",
    "не работает",
    "перестал",
    "перестала",
    "перестало",
)
MANUAL_REVIEW_TERMS = (
    "maybe",
    "probably",
    "unknown",
    "возможно",
    "кажется",
    "не уверен",
    "под вопросом",
)


def extract_post_claims(post: dict[str, object], profile_id: str) -> list[dict[str, object]]:
    """Extract deterministic first-pass claims from a normalized post."""

    text = str(post.get("text") or "")
    lowered = text.casefold()
    entities = [entity for entity in post.get("entities", []) if isinstance(entity, dict)]
    claims: list[dict[str, object]] = []

    root_actions = _entities_by_kind(entities, "root_action")
    recovery_actions = _entities_by_kind(entities, "recovery_action")
    fixes = _entities_by_kind(entities, "fix")
    warnings = _entities_by_kind(entities, "warning")
    context_labels = _context_labels(entities, lowered)
    condition_labels = _condition_labels(lowered)
    risk_labels = _risk_labels(entities, lowered)
    freshness_context = _freshness_context(post, lowered)
    manual_review_required = any(term in lowered for term in MANUAL_REVIEW_TERMS)

    for action in root_actions:
        action_label = str(action.get("value") or "")
        target_labels = _targets_for_action(action_label, entities, fallback_kinds={"file"})
        claims.append(
            _claim(
                post,
                profile_id,
                claim_kind="method",
                method_kind="root",
                action_label=action_label,
                target_labels=target_labels,
                tool_labels=_tool_labels(entities, ROOT_METHOD_TOOLS),
                context_labels=context_labels,
                condition_labels=condition_labels,
                risk_labels=risk_labels,
                warning_labels=[str(item.get("value")) for item in warnings],
                freshness_context=freshness_context,
                confidence=0.72,
                extraction_rule="root_action_entity_v1",
                manual_review_required=manual_review_required,
                evidence_span=_evidence_span(text, action_label),
            )
        )

    for action in recovery_actions:
        action_label = str(action.get("value") or "")
        target_labels = _targets_for_action(action_label, entities, fallback_kinds={"file"})
        claims.append(
            _claim(
                post,
                profile_id,
                claim_kind="method",
                method_kind="recovery",
                action_label=action_label,
                target_labels=target_labels,
                tool_labels=_tool_labels(entities, RECOVERY_METHOD_TOOLS),
                context_labels=context_labels,
                condition_labels=condition_labels,
                risk_labels=risk_labels,
                warning_labels=[str(item.get("value")) for item in warnings],
                freshness_context=freshness_context,
                confidence=0.72,
                extraction_rule="recovery_action_entity_v1",
                manual_review_required=manual_review_required,
                evidence_span=_evidence_span(text, action_label),
            )
        )

    for fix in fixes:
        action_label = str(fix.get("value") or "")
        target_labels = _targets_for_action(action_label, entities, fallback_kinds={"file", "issue"})
        claims.append(
            _claim(
                post,
                profile_id,
                claim_kind="method",
                method_kind="issue_recovery",
                action_label=action_label,
                target_labels=target_labels,
                tool_labels=_tool_labels(entities),
                context_labels=context_labels,
                condition_labels=condition_labels,
                risk_labels=risk_labels,
                warning_labels=[str(item.get("value")) for item in warnings],
                freshness_context=freshness_context,
                confidence=0.62,
                extraction_rule="fix_entity_v1",
                manual_review_required=manual_review_required,
                evidence_span=_evidence_span(text, action_label),
            )
        )

    warning_claims = list(warnings)
    if _has_warning_language(lowered) and not warning_claims:
        warning_claims.append({"kind": "warning", "value": _warning_excerpt(text)})
    for warning in warning_claims:
        warning_label = str(warning.get("value") or "")
        target_labels = _warning_target_labels(warning_label, entities)
        claims.append(
            _claim(
                post,
                profile_id,
                claim_kind="warning",
                method_kind="risk_warning",
                action_label=warning_label,
                target_labels=target_labels,
                tool_labels=_tool_labels(entities),
                context_labels=context_labels,
                condition_labels=condition_labels,
                risk_labels=risk_labels or ["unsafe_without_matching_context"],
                warning_labels=[warning_label],
                freshness_context=freshness_context,
                confidence=0.7 if warnings else 0.55,
                extraction_rule="warning_entity_or_language_v1",
                manual_review_required=manual_review_required or not warnings,
                evidence_span=_evidence_span(text, warning_label),
            )
        )

    if _has_update_language(lowered):
        target_labels = _target_labels(entities, kinds={"file", "firmware_family", "firmware_version", "build_id"})
        claims.append(
            _claim(
                post,
                profile_id,
                claim_kind="status",
                method_kind="freshness_update",
                action_label=_status_label(lowered),
                target_labels=target_labels,
                tool_labels=_tool_labels(entities),
                context_labels=context_labels,
                condition_labels=condition_labels,
                risk_labels=risk_labels,
                warning_labels=[],
                freshness_context={**freshness_context, "source_updates_prior_claims": True},
                confidence=0.58,
                extraction_rule="freshness_language_v1",
                manual_review_required=True,
                evidence_span=_evidence_span(text, _status_label(lowered)),
            )
        )

    return _dedupe_claims(claims)


def assign_freshness_windows(claims: list[dict[str, object]]) -> None:
    """Annotate claims with early/middle/late/latest-window context in-place."""

    if not claims:
        return
    ranked = sorted(claims, key=lambda claim: (_claim_time_sort_key(claim), str(claim.get("claim_id"))))
    count = len(ranked)
    related_by_key: dict[str, list[dict[str, object]]] = {}
    for claim in ranked:
        related_by_key.setdefault(_relation_key(claim), []).append(claim)
    for index, claim in enumerate(ranked):
        freshness = claim.setdefault("freshness_context", {})
        if not isinstance(freshness, dict):
            freshness = {}
            claim["freshness_context"] = freshness
        if count == 1 or index == count - 1:
            window = "latest_window"
        elif index < count / 3:
            window = "early"
        elif index < (2 * count) / 3:
            window = "middle"
        else:
            window = "late"
        newer_related = [
            str(other.get("claim_id"))
            for other in related_by_key.get(_relation_key(claim), [])
            if _claim_time_sort_key(other) > _claim_time_sort_key(claim)
        ]
        freshness["profile_window"] = window
        freshness["newer_related_claim_ids"] = newer_related
        freshness["newer_related_claims_exist"] = bool(newer_related)
        freshness["possibly_superseded"] = bool(newer_related)


def graph_nodes_for_claims(claims: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Return claim graph nodes keyed by node_id."""

    nodes: dict[str, dict[str, object]] = {}
    for claim in claims:
        claim_id = str(claim["claim_id"])
        source_url = str(claim.get("source_url") or "")
        nodes[claim_id] = {
            "schema": "aoa_4pda_graph_node_v1",
            "node_id": claim_id,
            "kind": "claim",
            "label": str(claim.get("label") or claim.get("action") or claim_id),
            "source_refs": [source_url] if source_url else [],
            "confidence": float(claim.get("confidence") or 0.0),
            "claim": claim,
        }
        method_id = str(claim.get("method_id") or "")
        if method_id:
            _upsert_node(nodes, method_id, "method", str(claim.get("method_label") or method_id), source_url, 0.65)
        action_node = _action_node_id(claim.get("action"))
        if action_node:
            _upsert_node(nodes, action_node, "action", str(claim.get("action")), source_url, 0.65)
        for label in _strings(claim.get("target_labels", [])):
            _upsert_node(nodes, _target_node_id(label), "target", label, source_url, 0.65)
        for label in _strings(claim.get("tool_labels", [])):
            _upsert_node(nodes, _tool_node_id(label), "tool", label, source_url, 0.65)
        for label in _strings(claim.get("condition_labels", [])):
            _upsert_node(nodes, _condition_node_id(label), "condition", label, source_url, 0.6)
        for label in _strings(claim.get("applicability_context", [])):
            _upsert_node(nodes, _context_node_id(label), "applicability_context", label, source_url, 0.6)
        for label in _strings(claim.get("risk_labels", [])):
            _upsert_node(nodes, _risk_node_id(label), "risk", label, source_url, 0.6)
        for label in _strings(claim.get("warning_labels", [])):
            _upsert_node(nodes, _warning_node_id(label), "warning", label, source_url, 0.65)
    return nodes


def relation_edges_for_claims(claims: list[dict[str, object]]) -> list[dict[str, object]]:
    """Build deterministic claim relation edges with audit metadata."""

    edges: list[dict[str, object]] = []
    for claim in claims:
        claim_id = str(claim["claim_id"])
        post_node = f"post:{claim.get('source_post_id')}"
        source_kind = "source_warns_about_claim" if claim.get("claim_kind") == "warning" else "source_supports_claim"
        _append_claim_edge(edges, source_kind, post_node, claim_id, claim, confidence=float(claim.get("confidence") or 0.0))
        if claim.get("claim_kind") == "status":
            _append_claim_edge(edges, "source_updates_claim", post_node, claim_id, claim, confidence=0.55)
        _append_claim_edge(edges, "post_mentions_claim", post_node, claim_id, claim, confidence=float(claim.get("confidence") or 0.0))

        method_id = str(claim.get("method_id") or "")
        action_node = _action_node_id(claim.get("action"))
        if action_node:
            _append_claim_edge(edges, "claim_applies_to_context", claim_id, action_node, claim, confidence=0.55)
        for label in _strings(claim.get("applicability_context", [])):
            _append_claim_edge(edges, "claim_applies_to_context", claim_id, _context_node_id(label), claim, confidence=0.55)
        if method_id:
            _append_claim_edge(edges, "claim_refines_claim", claim_id, method_id, claim, confidence=0.45)
            for label in _strings(claim.get("tool_labels", [])):
                _append_claim_edge(edges, "method_uses_tool", method_id, _tool_node_id(label), claim, confidence=0.6)
            for label in _strings(claim.get("target_labels", [])):
                _append_claim_edge(edges, "method_targets_object", method_id, _target_node_id(label), claim, confidence=0.65)
            for label in _strings(claim.get("condition_labels", [])):
                _append_claim_edge(edges, "method_requires_condition", method_id, _condition_node_id(label), claim, confidence=0.5)
        if claim.get("claim_kind") == "warning":
            for label in _strings(claim.get("target_labels", [])):
                _append_claim_edge(edges, "warning_targets_object", claim_id, _target_node_id(label), claim, confidence=0.62)
            if action_node:
                _append_claim_edge(edges, "warning_targets_action", claim_id, action_node, claim, confidence=0.55)

    _append_cross_claim_edges(edges, claims)
    return edges


def claim_graph_stats(claims: list[dict[str, object]], edges: list[dict[str, object]]) -> dict[str, object]:
    """Return receipt/audit counters for claim graph semantics."""

    relation_counts: dict[str, int] = {}
    confidence_buckets = {"high": 0, "medium": 0, "low": 0}
    for edge in edges:
        kind = str(edge.get("kind") or "")
        if kind in CLAIM_RELATION_KINDS:
            relation_counts[kind] = relation_counts.get(kind, 0) + 1
    for claim in claims:
        confidence = float(claim.get("confidence") or 0.0)
        if confidence >= 0.7:
            confidence_buckets["high"] += 1
        elif confidence >= 0.5:
            confidence_buckets["medium"] += 1
        else:
            confidence_buckets["low"] += 1
    return {
        "extractor_version": CLAIM_EXTRACTOR_VERSION,
        "relation_extractor_version": RELATION_EXTRACTOR_VERSION,
        "claim_count": len(claims),
        "method_count": sum(1 for claim in claims if claim.get("claim_kind") == "method"),
        "warning_count": sum(1 for claim in claims if claim.get("claim_kind") == "warning"),
        "applicability_context_count": len(
            {
                context
                for claim in claims
                for context in _strings(claim.get("applicability_context", []))
            }
        ),
        "supersedes_count": relation_counts.get("claim_supersedes_claim", 0),
        "contradicts_count": relation_counts.get("claim_contradicts_claim", 0),
        "contextualizes_count": relation_counts.get("claim_contextualizes_claim", 0),
        "warning_relation_count": relation_counts.get("source_warns_about_claim", 0)
        + relation_counts.get("warning_targets_object", 0)
        + relation_counts.get("warning_targets_action", 0),
        "manual_review_candidate_count": sum(1 for claim in claims if claim.get("manual_review_required") is True),
        "confidence_buckets": confidence_buckets,
        "relation_counts": relation_counts,
    }


def _claim(
    post: dict[str, object],
    profile_id: str,
    *,
    claim_kind: str,
    method_kind: str,
    action_label: str,
    target_labels: list[str],
    tool_labels: list[str],
    context_labels: list[str],
    condition_labels: list[str],
    risk_labels: list[str],
    warning_labels: list[str],
    freshness_context: dict[str, object],
    confidence: float,
    extraction_rule: str,
    manual_review_required: bool,
    evidence_span: dict[str, object],
) -> dict[str, object]:
    action = _action_name(action_label)
    source_url = str(post.get("source_url") or "")
    post_id = str(post.get("post_id") or "")
    label = _claim_label(action_label, target_labels, tool_labels, context_labels)
    method_id = f"method:{profile_id}:{_slug(method_kind)}:{_slug(action)}:{_slug('_'.join(target_labels) or action_label)}"
    claim_id = f"claim:{profile_id}:{post_id}:{_slug(claim_kind)}:{_slug(label)}"
    if len(claim_id) > 140:
        claim_id = f"claim:{profile_id}:{post_id}:{_slug(claim_kind)}:{hashlib.sha256(label.encode('utf-8')).hexdigest()[:16]}"
    return {
        "schema": "aoa_connector_claim_v1",
        "claim_id": claim_id,
        "claim_kind": claim_kind,
        "method_id": method_id,
        "method_kind": method_kind,
        "method_label": method_kind.replace("_", " "),
        "action": action,
        "label": label,
        "target_labels": sorted(set(target_labels)),
        "tool_labels": sorted(set(tool_labels)),
        "condition_labels": sorted(set(condition_labels)),
        "applicability_context": sorted(set(context_labels)),
        "risk_labels": sorted(set(risk_labels)),
        "warning_labels": sorted(set(warning_labels)),
        "source_post": {
            "post_id": post_id,
            "topic_id": post.get("topic_id"),
            "source_url": source_url,
            "posted_at": post.get("posted_at"),
            "captured_at": post.get("captured_at"),
        },
        "source_post_id": post_id,
        "topic_id": post.get("topic_id"),
        "source_url": source_url,
        "posted_at": post.get("posted_at"),
        "captured_at": post.get("captured_at"),
        "evidence_span": evidence_span,
        "freshness_context": freshness_context,
        "confidence": confidence,
        "confidence_basis": {
            "basis": "deterministic_entity_and_language_heuristic",
            "extractor_version": CLAIM_EXTRACTOR_VERSION,
        },
        "extraction_rule": extraction_rule,
        "manual_review_required": manual_review_required,
        "relation_key": "",
    } | {"relation_key": _relation_key_from_values(action, target_labels, tool_labels)}


def _append_cross_claim_edges(edges: list[dict[str, object]], claims: list[dict[str, object]]) -> None:
    for claim in claims:
        for other in claims:
            if claim is other:
                continue
            if not _related_claims(claim, other):
                continue
            claim_newer = _claim_time_sort_key(claim) > _claim_time_sort_key(other)
            if claim.get("claim_kind") == "warning" and other.get("claim_kind") != "warning":
                _append_claim_edge(
                    edges,
                    "claim_contextualizes_claim",
                    str(claim["claim_id"]),
                    str(other["claim_id"]),
                    claim,
                    other,
                    confidence=0.55,
                    reason="warning shares target/action context with method claim",
                    manual_review_required=False,
                )
                if _is_strong_warning(claim):
                    _append_claim_edge(
                        edges,
                        "claim_contradicts_claim",
                        str(claim["claim_id"]),
                        str(other["claim_id"]),
                        claim,
                        other,
                        confidence=0.52,
                        reason="strong warning may contradict an ordinary method answer",
                        manual_review_required=True,
                    )
                    _append_claim_edge(
                        edges,
                        "claim_deprecated_for_context",
                        str(other["claim_id"]),
                        str(claim["claim_id"]),
                        claim,
                        other,
                        confidence=0.5,
                        reason="method must be demoted when warning applies to its target/context",
                        manual_review_required=True,
                    )
            if claim_newer and _has_freshness_update(claim):
                _append_claim_edge(
                    edges,
                    "claim_supersedes_claim",
                    str(claim["claim_id"]),
                    str(other["claim_id"]),
                    claim,
                    other,
                    confidence=0.5,
                    reason="newer related claim has update/current/no-longer language",
                    manual_review_required=True,
                )
                _append_claim_edge(
                    edges,
                    "claim_contextualizes_claim",
                    str(claim["claim_id"]),
                    str(other["claim_id"]),
                    claim,
                    other,
                    confidence=0.5,
                    reason="newer related claim contextualizes older local evidence",
                    manual_review_required=True,
                )


def _append_claim_edge(
    edges: list[dict[str, object]],
    kind: str,
    from_node: str,
    to_node: str,
    claim: dict[str, object],
    other_claim: dict[str, object] | None = None,
    *,
    confidence: float,
    reason: str | None = None,
    manual_review_required: bool | None = None,
) -> None:
    if not from_node or not to_node:
        return
    source_refs = _unique(
        [
            str(claim.get("source_url") or ""),
            str(other_claim.get("source_url") or "") if other_claim else "",
        ]
    )
    source_post_ids = _unique(
        [
            str(claim.get("source_post_id") or ""),
            str(other_claim.get("source_post_id") or "") if other_claim else "",
        ]
    )
    edge_id = f"{from_node}->{to_node}:{kind}:{hashlib.sha256('|'.join(source_refs + source_post_ids).encode('utf-8')).hexdigest()[:10]}"
    if any(edge.get("edge_id") == edge_id for edge in edges):
        return
    freshness_basis = "source_post_and_capture_metadata"
    edge = {
        "schema": "aoa_4pda_graph_edge_v1",
        "edge_id": edge_id,
        "kind": kind,
        "from_node": from_node,
        "to_node": to_node,
        "source_refs": source_refs,
        "source_post_ids": source_post_ids,
        "confidence": round(confidence, 6),
        "extraction_basis": str(claim.get("extraction_rule") or CLAIM_EXTRACTOR_VERSION),
        "relation_reason": reason or _default_relation_reason(kind, claim),
        "freshness_basis": freshness_basis,
        "posted_at": claim.get("posted_at"),
        "captured_at": claim.get("captured_at"),
        "manual_review_required": (
            bool(manual_review_required)
            if manual_review_required is not None
            else bool(claim.get("manual_review_required"))
        ),
    }
    if other_claim:
        edge["related_posted_at"] = other_claim.get("posted_at")
        edge["related_captured_at"] = other_claim.get("captured_at")
    edges.append(edge)


def _default_relation_reason(kind: str, claim: dict[str, object]) -> str:
    if kind == "post_mentions_claim":
        return "source post yielded this extracted claim"
    if kind.startswith("source_"):
        return "source post provides direct evidence for this claim"
    if kind.startswith("method_"):
        return "method claim carries extracted tool/target/condition structure"
    if kind.startswith("warning_"):
        return "warning claim carries extracted target/action structure"
    if kind.startswith("claim_"):
        return "claim relation inferred from shared target/action/freshness context"
    return str(claim.get("extraction_rule") or CLAIM_EXTRACTOR_VERSION)


def _related_claims(left: dict[str, object], right: dict[str, object]) -> bool:
    if left.get("source_post_id") == right.get("source_post_id"):
        return False
    left_targets = set(_strings(left.get("target_labels", [])))
    right_targets = set(_strings(right.get("target_labels", [])))
    if left_targets and right_targets and left_targets.intersection(right_targets):
        return True
    return str(left.get("relation_key") or "") == str(right.get("relation_key") or "")


def _has_freshness_update(claim: dict[str, object]) -> bool:
    freshness = claim.get("freshness_context", {})
    if isinstance(freshness, dict) and freshness.get("source_updates_prior_claims"):
        return True
    label = str(claim.get("label") or "").casefold()
    return any(term in label for term in UPDATE_TERMS + NEGATIVE_STATUS_TERMS)


def _is_strong_warning(claim: dict[str, object]) -> bool:
    text = " ".join(_strings(claim.get("warning_labels", [])) + [str(claim.get("label") or "")]).casefold()
    return any(term in text for term in WARNING_TERMS + NEGATIVE_STATUS_TERMS)


def _entities_by_kind(entities: list[dict[str, object]], kind: str) -> list[dict[str, object]]:
    return [entity for entity in entities if entity.get("kind") == kind]


def _tool_labels(entities: list[dict[str, object]], allowed: set[str] | None = None) -> list[str]:
    values = [str(entity.get("value") or "") for entity in _entities_by_kind(entities, "tool")]
    if allowed:
        values = [value for value in values if value in allowed]
    return sorted(set(value for value in values if value))


def _target_labels(entities: list[dict[str, object]], *, kinds: set[str]) -> list[str]:
    return sorted({str(entity.get("value")) for entity in entities if entity.get("kind") in kinds and entity.get("value")})


def _targets_for_action(action_label: str, entities: list[dict[str, object]], *, fallback_kinds: set[str]) -> list[str]:
    lowered = action_label.casefold()
    direct = [
        str(entity.get("value"))
        for entity in entities
        if entity.get("kind") in fallback_kinds and str(entity.get("value") or "").casefold() in lowered
    ]
    return sorted(set(direct or _target_labels(entities, kinds=fallback_kinds)))


def _warning_target_labels(warning_label: str, entities: list[dict[str, object]]) -> list[str]:
    lowered = warning_label.casefold()
    direct = [
        str(entity.get("value"))
        for entity in entities
        if entity.get("kind") in {"file", "codename", "device", "firmware_family", "firmware_version", "build_id", "tool"}
        and str(entity.get("value") or "").casefold() in lowered
    ]
    if direct:
        return sorted(set(direct))
    return _target_labels(entities, kinds={"file", "codename", "firmware_family", "firmware_version"})


def _context_labels(entities: list[dict[str, object]], lowered: str) -> list[str]:
    labels = _target_labels(entities, kinds={"device", "device_model", "codename", "firmware_family", "firmware_version", "build_id"})
    if "global" in lowered or "глобал" in lowered:
        labels.append("region:global")
    if "eea" in lowered or "europe" in lowered or "европ" in lowered:
        labels.append("region:eea")
    if "china" in lowered or "китай" in lowered:
        labels.append("region:china")
    if "после обнов" in lowered or "after update" in lowered:
        labels.append("after_update")
    return sorted(set(labels))


def _condition_labels(lowered: str) -> list[str]:
    labels: list[str] = []
    if "bootloader" in lowered or "загрузчик" in lowered:
        if "unlock" in lowered or "разблок" in lowered:
            labels.append("bootloader_unlocked")
    if "fastbootd" in lowered:
        labels.append("fastbootd_available")
    if "matching" in lowered or "родной" in lowered or "стоковой прошивки" in lowered:
        labels.append("matching_firmware_required")
    return sorted(set(labels))


def _risk_labels(entities: list[dict[str, object]], lowered: str) -> list[str]:
    labels = _target_labels(entities, kinds={"issue"})
    if "fastbootd" in lowered and any(term in lowered for term in ("кирпич", "brick")):
        labels.append("brick_fastbootd")
    if any(term in lowered for term in ("не ставить", "do not install", "не прошивать")):
        labels.append("unsafe_flash")
    return sorted(set(labels))


def _freshness_context(post: dict[str, object], lowered: str) -> dict[str, object]:
    return {
        "posted_at": post.get("posted_at"),
        "captured_at": post.get("captured_at"),
        "source_freshness": "source_post_and_capture_metadata",
        "profile_window": "unknown_until_graph_build",
        "has_update_language": _has_update_language(lowered),
        "has_negative_status_language": any(term in lowered for term in NEGATIVE_STATUS_TERMS),
    }


def _has_update_language(lowered: str) -> bool:
    return any(term in lowered for term in UPDATE_TERMS + NEGATIVE_STATUS_TERMS)


def _has_warning_language(lowered: str) -> bool:
    return any(term in lowered for term in WARNING_TERMS)


def _warning_excerpt(text: str) -> str:
    clean = " ".join(text.split())
    lowered = clean.casefold()
    indexes = [lowered.find(term) for term in WARNING_TERMS if lowered.find(term) >= 0]
    if not indexes:
        return clean[:180]
    start = max(0, min(indexes) - 50)
    return clean[start : start + 220].strip()


def _status_label(lowered: str) -> str:
    if any(term in lowered for term in NEGATIVE_STATUS_TERMS):
        return "no longer works for current context"
    if "после обнов" in lowered or "after update" in lowered:
        return "after update context changes applicability"
    return "current update context"


def _action_name(action_label: str) -> str:
    lowered = action_label.casefold()
    if "restore" in lowered or "восстанов" in lowered or "верн" in lowered:
        return "restore"
    if "patch" in lowered or "патч" in lowered:
        return "patch"
    if "flash" in lowered or "прош" in lowered or "install" in lowered:
        return "flash"
    if "no longer" in lowered or "не работает" in lowered:
        return "status_update"
    if any(term in lowered for term in WARNING_TERMS):
        return "warn"
    return _slug(action_label) or "claim"


def _claim_label(action_label: str, target_labels: list[str], tool_labels: list[str], context_labels: list[str]) -> str:
    bits = [action_label]
    if target_labels:
        bits.append("targets " + ", ".join(target_labels[:3]))
    if tool_labels:
        bits.append("uses " + ", ".join(tool_labels[:3]))
    if context_labels:
        bits.append("context " + ", ".join(context_labels[:3]))
    return " | ".join(bit for bit in bits if bit)


def _evidence_span(text: str, needle: str) -> dict[str, object]:
    clean = " ".join(text.split())
    lowered = clean.casefold()
    needle_lower = str(needle or "").casefold()
    start = lowered.find(needle_lower) if needle_lower else -1
    if start < 0:
        start = 0
    end = min(len(clean), start + 260)
    return {
        "type": "excerpt",
        "char_start": start,
        "char_end": end,
        "text": clean[start:end],
    }


def _dedupe_claims(claims: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    unique: list[dict[str, object]] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "")
        if claim_id in seen:
            continue
        seen.add(claim_id)
        unique.append(claim)
    return unique


def _relation_key(claim: dict[str, object]) -> str:
    existing = str(claim.get("relation_key") or "")
    if existing:
        return existing
    return _relation_key_from_values(str(claim.get("action") or ""), _strings(claim.get("target_labels", [])), _strings(claim.get("tool_labels", [])))


def _relation_key_from_values(action: str, target_labels: list[str], tool_labels: list[str]) -> str:
    target_key = "|".join(sorted(_slug(value) for value in target_labels))
    tool_key = "|".join(sorted(_slug(value) for value in tool_labels))
    return f"{_slug(action)}:{target_key}:{tool_key}"


def _claim_time_sort_key(claim: dict[str, object]) -> tuple[int, str, int]:
    post_order = _post_order(claim.get("source_post_id"))
    for key in ["posted_at", "captured_at"]:
        parsed = _parse_time(claim.get(key))
        if parsed is not None:
            return (1, parsed.isoformat(), post_order)
    return (0, str(claim.get("claim_id") or ""), post_order)


def _post_order(value: object) -> int:
    digits = re.sub(r"\D+", "", str(value or ""))
    try:
        return int(digits)
    except ValueError:
        return 0


def _parse_time(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%d.%m.%y, %H:%M", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _upsert_node(
    nodes: dict[str, dict[str, object]],
    node_id: str,
    kind: str,
    label: str,
    source_url: str,
    confidence: float,
) -> None:
    node = nodes.setdefault(
        node_id,
        {
            "schema": "aoa_4pda_graph_node_v1",
            "node_id": node_id,
            "kind": kind,
            "label": label,
            "source_refs": [],
            "confidence": confidence,
        },
    )
    if source_url and source_url not in node["source_refs"]:
        node["source_refs"].append(source_url)


def _action_node_id(label: object) -> str:
    text = str(label or "").strip()
    return f"action:{_slug(text)}" if text else ""


def _target_node_id(label: str) -> str:
    return f"target:{_slug(label)}"


def _tool_node_id(label: str) -> str:
    return f"tool:{_slug(label)}"


def _condition_node_id(label: str) -> str:
    return f"condition:{_slug(label)}"


def _context_node_id(label: str) -> str:
    return f"context:{_slug(label)}"


def _risk_node_id(label: str) -> str:
    return f"risk:{_slug(label)}"


def _warning_node_id(label: str) -> str:
    digest = hashlib.sha256(label.encode("utf-8")).hexdigest()[:12]
    return f"warning:{_slug(label)[:60]}:{digest}"


def _slug(value: object) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"[^a-z0-9а-яё]+", "_", text, flags=re.I).strip("_")
    return text or "unknown"


def _strings(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item).strip() for item in items if str(item).strip()]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique
