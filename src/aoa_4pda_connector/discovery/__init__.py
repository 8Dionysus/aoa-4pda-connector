"""No-network discovery audit over already-stored public snapshots."""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from aoa_4pda_connector.config import LOCAL_STATE_DIR, StorageRoots, find_repo_root
from aoa_4pda_connector.fetch import canonical_topic_url, topic_id_from_url, topic_page_start_from_url, topic_page_url
from aoa_4pda_connector.parse import extract_title
from aoa_4pda_connector.policy import is_url_allowed


DISCOVERY_TARGET = "reference-profile-discovery-v1"
SEED_REVIEW_TARGET = "reference-profile-seed-review-v1"
HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
PLAIN_URL_RE = re.compile(r"""https?://(?:www\.)?4pda\.(?:to|ru)/forum/index\.php\?[^"'\s<>]+""", re.I)
BASE_URL = "https://4pda.to/forum/"
MAX_EVIDENCE_VALUES = 8
DEFAULT_REVIEW_MANIFESTS = {
    "xiaomi-13t": "connector/seeds/reviews/xiaomi_13t_discovery_review.json",
}


def audit_profile_discovery(
    profile_id: str,
    repo_root: Path | None = None,
    roots: StorageRoots | None = None,
    *,
    run: str = "latest",
    limit: int = 25,
) -> dict[str, object]:
    """Return public-topic discovery candidates from stored crawl snapshots."""

    root = repo_root or find_repo_root()
    storage_roots = roots or StorageRoots.from_env(root)
    profile_path = root / "connector" / "profiles" / f"{profile_id}.yaml"
    if not profile_path.is_file():
        return {
            "schema": "aoa_4pda_discovery_audit_v1",
            "target_status": DISCOVERY_TARGET,
            "status": "error",
            "profile_id": profile_id,
            "run": run,
            "error": f"profile not found: {profile_path.relative_to(root)}",
            "network_touched": False,
        }

    profile = _read_profile(profile_path)
    seed_rel = str(profile.get("seed_file", "connector/seeds/starter_topics.yaml"))
    seed_path = root / seed_rel
    seeds = _read_seed_urls(seed_path) if seed_path.is_file() else []
    default_pages = _int_value(profile.get("max_pages_per_topic"), 1)
    seed_urls = {_canonical_url(seed["url"]) for seed in seeds if seed.get("url")}
    seed_topic_ids = {topic_id_from_url(seed["url"]) for seed in seeds if seed.get("url")}
    covered_seed_urls = _covered_seed_urls(seeds, default_pages)
    covered_seed_windows = _covered_seed_windows(seeds, default_pages)
    profile_terms = _profile_terms(profile)
    receipt = _load_receipt(storage_roots, run, "crawl")
    snapshots = receipt.get("snapshots", []) if isinstance(receipt.get("snapshots"), list) else []

    grouped: dict[str, dict[str, object]] = {}
    denied: dict[str, int] = defaultdict(int)
    known_link_count = 0
    covered_seed_window_link_count = 0
    inspected_snapshots = 0
    missing_snapshot_paths: list[str] = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        path = Path(str(snapshot.get("path", "")))
        if not path.is_file():
            if snapshot.get("path"):
                missing_snapshot_paths.append(str(path))
            continue
        inspected_snapshots += 1
        source = {
            "seed_id": snapshot.get("seed_id"),
            "label": snapshot.get("label"),
            "source_url": snapshot.get("url"),
            "page_start": snapshot.get("page_start"),
            "path": str(path),
        }
        for occurrence in _extract_topic_like_urls(path):
            normalized = _normalized_for_policy(str(occurrence.get("url", "")))
            if not normalized:
                continue
            if not is_url_allowed(normalized):
                denied[normalized] += 1
                continue
            canonical = _canonical_url(normalized)
            if not canonical:
                continue
            if canonical in seed_urls:
                known_link_count += 1
                continue
            if canonical in covered_seed_urls or _topic_window_key(canonical) in covered_seed_windows:
                covered_seed_window_link_count += 1
                continue
            item = grouped.setdefault(canonical, _candidate(canonical, seed_topic_ids, source))
            item["source_count"] = int(item["source_count"]) + 1
            _append_unique(item["source_seed_ids"], source["seed_id"])
            _append_unique(item["source_urls"], source["source_url"])
            _append_unique_limited(item["source_labels"], source["label"])
            _record_occurrence(item, source, occurrence)

    for item in grouped.values():
        _apply_review_hint(item, profile_terms)
    candidates = sorted(
        grouped.values(),
        key=lambda item: (
            _review_priority_sort(str(item.get("review_priority", "low"))),
            0 if item.get("candidate_kind") == "unseeded_topic" else 1,
            -int(item.get("source_count", 0)),
            str(item.get("topic_id")),
            int(item.get("page_start", 0)),
        ),
    )
    if not receipt:
        status = "missing_run"
    elif candidates:
        status = "needs_seed_review"
    else:
        status = "no_new_candidates"

    return {
        "schema": "aoa_4pda_discovery_audit_v1",
        "target_status": DISCOVERY_TARGET,
        "status": status,
        "profile_id": profile_id,
        "run": run,
        "repo_root": str(root),
        "storage_mode": storage_roots.mode,
        "local_state_dir": LOCAL_STATE_DIR,
        "storage_roots": storage_roots.as_dict(),
        "profile": {
            "path": str(profile_path.relative_to(root)),
            "seed_file": seed_rel,
            "target_label": profile.get("target_label"),
            "target_codename": profile.get("target_codename"),
            "target_terms": profile_terms,
        },
        "seed_state": {
            "seed_file_exists": seed_path.is_file(),
            "seed_count": len(seeds),
            "seed_topic_ids": sorted(seed_topic_ids),
            "seed_url_count": len(seed_urls),
            "covered_seed_window_count": len(covered_seed_windows),
        },
        "source_run": {
            "run_id": receipt.get("run_id"),
            "profile_id": receipt.get("profile_id"),
            "snapshot_count": len(snapshots),
            "inspected_snapshot_count": inspected_snapshots,
            "missing_snapshot_paths": missing_snapshot_paths,
            "network_touched": receipt.get("network_touched"),
        },
        "discovery": {
            "candidate_count": len(candidates),
            "unseeded_topic_count": sum(1 for item in candidates if item.get("candidate_kind") == "unseeded_topic"),
            "seed_topic_new_window_count": sum(
                1 for item in candidates if item.get("candidate_kind") == "seed_topic_new_window"
            ),
            "known_seed_link_count": known_link_count,
            "covered_seed_window_link_count": covered_seed_window_link_count,
            "denied_link_count": sum(denied.values()),
            "denied_links": [{"url": url, "count": count} for url, count in sorted(denied.items())[:limit]],
            "review_priority_counts": _review_priority_counts(candidates),
            "candidates": candidates[: max(0, limit)],
        },
        "checks": {
            "profile_exists": profile_path.is_file(),
            "seed_file_exists": seed_path.is_file(),
            "crawl_receipt_present": bool(receipt),
            "snapshots_available": inspected_snapshots > 0 if receipt else False,
            "public_candidates_allowed": all(is_url_allowed(str(item.get("url", ""))) for item in candidates),
            "covered_seed_windows_excluded_from_candidates": True,
            "network_touched": False,
        },
        "next_actions": _next_actions(status, candidates),
        "network_touched": False,
    }


def audit_profile_seed_review(
    profile_id: str,
    repo_root: Path | None = None,
    roots: StorageRoots | None = None,
    *,
    run: str = "latest",
    manifest: str | Path | None = None,
    limit: int = 25,
) -> dict[str, object]:
    """Return seed-review state for current discovery candidates."""

    root = repo_root or find_repo_root()
    storage_roots = roots or StorageRoots.from_env(root)
    review_path = _review_manifest_path(root, profile_id, manifest)
    discovery = audit_profile_discovery(profile_id, root, storage_roots, run=run, limit=10000)
    if discovery.get("status") == "error":
        return {
            "schema": "aoa_4pda_discovery_review_audit_v1",
            "target_status": SEED_REVIEW_TARGET,
            "status": "error",
            "profile_id": profile_id,
            "run": run,
            "manifest_path": str(review_path.relative_to(root)) if _is_relative_to(review_path, root) else str(review_path),
            "error": discovery.get("error", "discovery audit failed"),
            "network_touched": False,
        }

    candidates = list(_discovery_candidates(discovery))
    seed_urls, covered_seed_windows = _seed_coverage_for_profile(root, profile_id)
    manifest_payload = _load_review_manifest(review_path)
    manifest_exists = review_path.is_file()
    manifest_errors = _review_manifest_errors(manifest_payload, profile_id) if manifest_exists else []

    reviewed: list[dict[str, object]] = []
    accepted_missing: list[dict[str, object]] = []
    accepted_seeded: list[dict[str, object]] = []
    unreviewed: list[dict[str, object]] = []
    for candidate in candidates:
        review = _review_for_candidate(candidate, manifest_payload)
        decision = str(review.get("decision", "unreviewed"))
        item = _reviewed_candidate(candidate, review)
        reviewed.append(item)
        if decision == "unreviewed":
            unreviewed.append(item)
        elif decision == "accept" and _candidate_is_seeded(candidate, seed_urls, covered_seed_windows):
            accepted_seeded.append(item)
        elif decision == "accept":
            accepted_missing.append(item)

    stale_decisions = _stale_review_decisions(candidates, manifest_payload, seed_urls, covered_seed_windows)
    decision_counts = _decision_counts(reviewed)
    if discovery.get("status") == "missing_run":
        status = "missing_run"
    elif not manifest_exists:
        status = "missing_review"
    elif manifest_errors:
        status = "invalid_review"
    elif unreviewed:
        status = "needs_review"
    elif accepted_missing:
        status = "reviewed_pending_seed_update"
    else:
        status = "reviewed"

    return {
        "schema": "aoa_4pda_discovery_review_audit_v1",
        "target_status": SEED_REVIEW_TARGET,
        "status": status,
        "profile_id": profile_id,
        "run": run,
        "repo_root": str(root),
        "storage_mode": storage_roots.mode,
        "local_state_dir": LOCAL_STATE_DIR,
        "storage_roots": storage_roots.as_dict(),
        "manifest": {
            "path": str(review_path.relative_to(root)) if _is_relative_to(review_path, root) else str(review_path),
            "exists": manifest_exists,
            "schema": manifest_payload.get("schema"),
            "reviewed_at": manifest_payload.get("reviewed_at"),
            "source_discovery_run": manifest_payload.get("source_discovery_run"),
            "errors": manifest_errors,
        },
        "discovery": {
            "status": discovery.get("status"),
            "candidate_count": discovery.get("discovery", {}).get("candidate_count", 0),
            "reviewed_candidate_count": len([item for item in reviewed if item.get("decision") != "unreviewed"]),
            "unreviewed_count": len(unreviewed),
            "accepted_missing_from_seed_count": len(accepted_missing),
            "accepted_seeded_count": len(accepted_seeded),
            "stale_decision_count": len(stale_decisions),
            "decision_counts": decision_counts,
        },
        "accepted_missing_from_seed": accepted_missing[: max(0, limit)],
        "unreviewed_candidates": unreviewed[: max(0, limit)],
        "stale_decisions": stale_decisions[: max(0, limit)],
        "reviewed_candidates": reviewed[: max(0, limit)],
        "checks": {
            "manifest_exists": manifest_exists,
            "manifest_valid": manifest_exists and not manifest_errors,
            "discovery_run_present": discovery.get("status") != "missing_run",
            "all_current_candidates_reviewed": discovery.get("status") != "missing_run" and not unreviewed,
            "accepted_candidates_seeded": not accepted_missing,
            "network_touched": False,
        },
        "next_actions": _review_next_actions(status),
        "network_touched": False,
    }


def _candidate(canonical: str, seed_topic_ids: set[str], source: dict[str, object]) -> dict[str, object]:
    topic_id = topic_id_from_url(canonical)
    candidate_kind = "seed_topic_new_window" if topic_id in seed_topic_ids else "unseeded_topic"
    return {
        "url": canonical,
        "topic_id": topic_id,
        "page_start": int(topic_page_start_from_url(canonical)),
        "candidate_kind": candidate_kind,
        "source_count": 0,
        "source_seed_ids": [],
        "source_urls": [],
        "source_labels": [],
        "anchor_texts": [],
        "evidence_contexts": [],
        "target_hits": [],
        "source_target_hits": [],
        "review_priority": "unreviewed",
        "review_reasons": [],
        "first_seen_in": source,
    }


def _extract_topic_like_urls(path: Path) -> list[dict[str, object]]:
    data = path.read_bytes()
    text = _decode(data)
    title = extract_title(text)
    links = _HrefExtractor(title)
    links.feed(text)
    occurrences: list[dict[str, object]] = []
    seen: set[str] = set()
    for link in links.links:
        normalized = _normalized_for_policy(urljoin(BASE_URL, html.unescape(str(link.get("url", "")))))
        if normalized and normalized not in seen:
            seen.add(normalized)
            occurrences.append({**link, "url": normalized, "source_title": title})
    for url in PLAIN_URL_RE.findall(text):
        normalized = _normalized_for_policy(html.unescape(url))
        if normalized and normalized not in seen:
            seen.add(normalized)
            occurrences.append({"url": normalized, "anchor_text": "", "source_title": title})
    return occurrences


class _HrefExtractor(HTMLParser):
    def __init__(self, source_title: str) -> None:
        super().__init__()
        self.source_title = source_title
        self.links: list[dict[str, object]] = []
        self._active: list[dict[str, object]] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag_name == "a":
            attrs_map = {key.lower(): value or "" for key, value in attrs}
            href = attrs_map.get("href", "")
            if href:
                self._active.append({"url": href, "parts": []})

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not self._active:
            return
        text = _clean_inline_text(data)
        if text:
            self._active[-1]["parts"].append(text)

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.lower()
        if tag_name in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag_name == "a" and self._active:
            link = self._active.pop()
            anchor_text = _clean_inline_text(" ".join(str(part) for part in link.get("parts", [])))
            if not _useful_anchor_text(anchor_text):
                anchor_text = ""
            self.links.append(
                {
                    "url": str(link.get("url", "")),
                    "anchor_text": anchor_text,
                    "source_title": self.source_title,
                }
            )


def _normalized_for_policy(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return ""
    if parsed.netloc not in {"4pda.to", "4pda.ru", "www.4pda.to", "www.4pda.ru"}:
        return ""
    if not parsed.path.endswith("/index.php") or "/forum/" not in parsed.path:
        return ""
    return url


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    if "showtopic" not in parse_qs(parsed.query):
        return ""
    try:
        return canonical_topic_url(url)
    except Exception:  # noqa: BLE001 - malformed links are ignored by discovery audit.
        return ""


def _read_profile(path: Path) -> dict[str, object]:
    values: dict[str, object] = {"seed_file": "connector/seeds/starter_topics.yaml"}
    string_keys = {
        "seed_file",
        "target_label",
        "target_codename",
        "target_device_id",
        "target_model_aliases",
        "target_search_terms",
    }
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "max_pages_per_topic" and value:
            values[key] = _int_value(value, 1)
        elif key in string_keys and value:
            values[key] = value
    return values


def _read_seed_urls(path: Path) -> list[dict[str, str]]:
    seeds: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- id:"):
            if current:
                seeds.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif current and line.startswith("url:"):
            current["url"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("label:"):
            current["label"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("status:"):
            current["status"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("focus:"):
            current["focus"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("max_pages:"):
            current["max_pages"] = line.split(":", 1)[1].strip()
    if current:
        seeds.append(current)
    return [seed for seed in seeds if seed.get("url")]


def _load_receipt(roots: StorageRoots, run: str, kind: str) -> dict[str, object]:
    if roots.artifact is None:
        return {}
    receipt_dir = roots.artifact / "receipts"
    path = receipt_dir / f"latest_{kind}.json" if run == "latest" else receipt_dir / f"{run}.{kind}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _review_manifest_path(root: Path, profile_id: str, manifest: str | Path | None) -> Path:
    if manifest is not None:
        path = Path(manifest)
    else:
        path = Path(DEFAULT_REVIEW_MANIFESTS.get(profile_id, f"connector/seeds/reviews/{profile_id}_discovery_review.json"))
    return path if path.is_absolute() else root / path


def _load_review_manifest(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _review_manifest_errors(payload: dict[str, object], profile_id: str) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "aoa_4pda_discovery_review_manifest_v1":
        errors.append("unexpected or missing schema")
    if payload.get("profile_id") != profile_id:
        errors.append("profile_id does not match requested profile")
    for index, item in enumerate(payload.get("decisions", [])):
        if not isinstance(item, dict):
            errors.append(f"decisions[{index}] must be an object")
            continue
        if _normalize_decision(item.get("decision")) not in {"accept", "reject", "defer"}:
            errors.append(f"decisions[{index}] has invalid decision")
        if not item.get("url"):
            errors.append(f"decisions[{index}] is missing url")
    for index, item in enumerate(payload.get("rules", [])):
        if not isinstance(item, dict):
            errors.append(f"rules[{index}] must be an object")
            continue
        if _normalize_decision(item.get("decision")) not in {"accept", "reject", "defer"}:
            errors.append(f"rules[{index}] has invalid decision")
    return errors


def _discovery_candidates(discovery: dict[str, object]) -> list[dict[str, object]]:
    payload = discovery.get("discovery", {})
    if not isinstance(payload, dict):
        return []
    candidates = payload.get("candidates", [])
    return [item for item in candidates if isinstance(item, dict)]


def _review_for_candidate(candidate: dict[str, object], manifest: dict[str, object]) -> dict[str, object]:
    canonical = _canonical_url(str(candidate.get("url", "")))
    exact = _exact_review_decisions(manifest).get(canonical)
    if exact:
        return exact
    for rule in manifest.get("rules", []):
        if isinstance(rule, dict) and _rule_matches_candidate(rule, candidate):
            return {
                "decision": _normalize_decision(rule.get("decision")),
                "source": "rule",
                "rule_id": rule.get("id"),
                "rationale": rule.get("rationale", ""),
                "suggested_seed_status": rule.get("suggested_seed_status", ""),
            }
    return {"decision": "unreviewed", "source": "none", "rationale": ""}


def _exact_review_decisions(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    decisions: dict[str, dict[str, object]] = {}
    for item in manifest.get("decisions", []):
        if not isinstance(item, dict) or not item.get("url"):
            continue
        canonical = _canonical_url(str(item.get("url", "")))
        if not canonical:
            continue
        decisions[canonical] = {
            **item,
            "decision": _normalize_decision(item.get("decision")),
            "source": "exact",
        }
    return decisions


def _rule_matches_candidate(rule: dict[str, object], candidate: dict[str, object]) -> bool:
    candidate_kind = rule.get("candidate_kind")
    if candidate_kind and candidate_kind != candidate.get("candidate_kind"):
        return False
    topic_id = rule.get("topic_id")
    if topic_id and str(topic_id) != str(candidate.get("topic_id")):
        return False
    min_source_count = _int_value(rule.get("min_source_count"), 0)
    if min_source_count and int(candidate.get("source_count", 0)) < min_source_count:
        return False
    return True


def _reviewed_candidate(candidate: dict[str, object], review: dict[str, object]) -> dict[str, object]:
    return {
        "url": candidate.get("url"),
        "topic_id": candidate.get("topic_id"),
        "page_start": candidate.get("page_start"),
        "candidate_kind": candidate.get("candidate_kind"),
        "review_priority": candidate.get("review_priority"),
        "source_count": candidate.get("source_count"),
        "anchor_texts": candidate.get("anchor_texts", []),
        "source_labels": candidate.get("source_labels", []),
        "decision": review.get("decision", "unreviewed"),
        "decision_source": review.get("source", "none"),
        "rule_id": review.get("rule_id"),
        "rationale": review.get("rationale", ""),
        "suggested_seed_status": review.get("suggested_seed_status", ""),
        "suggested_seed": review.get("suggested_seed", {}),
    }


def _stale_review_decisions(
    candidates: list[dict[str, object]],
    manifest: dict[str, object],
    seed_urls: set[str],
    covered_seed_windows: set[tuple[str, int]],
) -> list[dict[str, object]]:
    current_urls = {_canonical_url(str(candidate.get("url", ""))) for candidate in candidates}
    stale = []
    for url, decision in sorted(_exact_review_decisions(manifest).items()):
        if url not in current_urls:
            if url in seed_urls or _topic_window_key(url) in covered_seed_windows:
                continue
            stale.append({"url": url, "decision": decision.get("decision"), "rationale": decision.get("rationale", "")})
    return stale


def _seed_coverage_for_profile(root: Path, profile_id: str) -> tuple[set[str], set[tuple[str, int]]]:
    profile_path = root / "connector" / "profiles" / f"{profile_id}.yaml"
    if not profile_path.is_file():
        return set(), set()
    profile = _read_profile(profile_path)
    seed_path = root / str(profile.get("seed_file", "connector/seeds/starter_topics.yaml"))
    seeds = _read_seed_urls(seed_path) if seed_path.is_file() else []
    default_pages = _int_value(profile.get("max_pages_per_topic"), 1)
    return _covered_seed_urls(seeds, default_pages), _covered_seed_windows(seeds, default_pages)


def _candidate_is_seeded(candidate: dict[str, object], seed_urls: set[str], covered_seed_windows: set[tuple[str, int]]) -> bool:
    url = _canonical_url(str(candidate.get("url", "")))
    return url in seed_urls or _topic_window_key(url) in covered_seed_windows


def _decision_counts(reviewed: list[dict[str, object]]) -> dict[str, int]:
    counts = {"accept": 0, "reject": 0, "defer": 0, "unreviewed": 0}
    for item in reviewed:
        decision = str(item.get("decision", "unreviewed"))
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _normalize_decision(value: object) -> str:
    raw = str(value or "").strip().casefold()
    aliases = {
        "accepted": "accept",
        "accept": "accept",
        "rejected": "reject",
        "reject": "reject",
        "deferred": "defer",
        "defer": "defer",
    }
    return aliases.get(raw, "unreviewed")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _decode(data: bytes) -> str:
    for encoding in ["windows-1251", "utf-8"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("windows-1251", errors="replace")


def _covered_seed_urls(seeds: list[dict[str, str]], default_pages: int) -> set[str]:
    urls: set[str] = set()
    for seed in seeds:
        for page_index in range(max(1, _int_value(seed.get("max_pages"), default_pages))):
            urls.add(canonical_topic_url(topic_page_url(seed["url"], page_index)))
    return urls


def _covered_seed_windows(seeds: list[dict[str, str]], default_pages: int) -> set[tuple[str, int]]:
    return {_topic_window_key(url) for url in _covered_seed_urls(seeds, default_pages)}


def _topic_window_key(url: str) -> tuple[str, int]:
    return (topic_id_from_url(url), _int_value(topic_page_start_from_url(url), 0))


def _record_occurrence(item: dict[str, object], source: dict[str, object], occurrence: dict[str, object]) -> None:
    _append_unique_limited(item["anchor_texts"], occurrence.get("anchor_text"))
    context = {
        "source_seed_id": source.get("seed_id"),
        "source_label": source.get("label"),
        "source_url": source.get("source_url"),
        "source_page_start": source.get("page_start"),
        "source_title": occurrence.get("source_title"),
        "anchor_text": occurrence.get("anchor_text"),
    }
    _append_unique_context(item["evidence_contexts"], context)


def _apply_review_hint(item: dict[str, object], profile_terms: list[str]) -> None:
    candidate_hit_text = " ".join(
        [
            str(item.get("url", "")),
            " ".join(str(value) for value in item.get("anchor_texts", [])),
            str(item.get("topic_id", "")),
        ]
    )
    source_hit_text = " ".join(
        [
            " ".join(str(value) for value in item.get("source_labels", [])),
            " ".join(str(value) for value in item.get("source_urls", [])),
            " ".join(str(value.get("source_title", "")) for value in item.get("evidence_contexts", []) if isinstance(value, dict)),
        ]
    )
    target_hits = _term_hits(candidate_hit_text, profile_terms)
    source_target_hits = _term_hits(source_hit_text, profile_terms)
    item["target_hits"] = target_hits
    item["source_target_hits"] = source_target_hits

    reasons: list[str] = []
    if target_hits:
        reasons.append("candidate link text or URL contains target terms")
    if source_target_hits:
        reasons.append("candidate was observed from target-profile snapshots")
    if item.get("candidate_kind") == "seed_topic_new_window":
        reasons.append("same topic id is seeded but this page window is outside the current seed plan")
    if int(item.get("source_count", 0)) >= 5:
        reasons.append("candidate repeats across several stored snapshots")

    if target_hits or item.get("candidate_kind") == "seed_topic_new_window" or int(item.get("source_count", 0)) >= 8:
        priority = "high"
    elif source_target_hits or int(item.get("source_count", 0)) >= 2:
        priority = "medium"
    else:
        priority = "low"

    item["review_priority"] = priority
    item["review_reasons"] = reasons or ["candidate needs manual relevance review before seed expansion"]


def _profile_terms(profile: dict[str, object]) -> list[str]:
    values: list[str] = []
    for key in [
        "target_device_id",
        "target_label",
        "target_codename",
        "target_model_aliases",
        "target_search_terms",
    ]:
        raw = profile.get(key)
        if not raw:
            continue
        values.extend(str(part).strip() for part in str(raw).split(","))
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = _clean_inline_text(value)
        key = normalized.casefold()
        if len(key) < 2 or key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped


def _term_hits(text: str, terms: list[str]) -> list[str]:
    folded = text.casefold()
    return [term for term in terms if term.casefold() in folded]


def _review_priority_counts(candidates: list[dict[str, object]]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for candidate in candidates:
        priority = str(candidate.get("review_priority", "low"))
        counts[priority] = counts.get(priority, 0) + 1
    return counts


def _review_priority_sort(priority: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(priority, 3)


def _append_unique(values: list[object], value: object) -> None:
    if value is None:
        return
    if value not in values:
        values.append(value)


def _append_unique_limited(values: list[object], value: object, limit: int = MAX_EVIDENCE_VALUES) -> None:
    if value is None or value == "":
        return
    if value not in values and len(values) < limit:
        values.append(value)


def _append_unique_context(values: list[object], context: dict[str, object], limit: int = MAX_EVIDENCE_VALUES) -> None:
    if context not in values and len(values) < limit:
        values.append(context)


def _clean_inline_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _useful_anchor_text(value: str) -> bool:
    if not value:
        return False
    return value not in {"<", ">", "«", "»", "‹", "›"}


def _int_value(value: object, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _next_actions(status: str, candidates: list[dict[str, object]]) -> list[str]:
    if status == "missing_run":
        return ["Create or restore a bounded crawl receipt before auditing discovery candidates."]
    if candidates:
        return [
            "Review high-priority discovery candidates with their anchor/source evidence before editing seeds.",
            "Add only accepted public topic windows to the profile seed file.",
            "Record rejected candidates in a follow-up note or keep them out of seeds with rationale.",
            "Re-run coverage and refresh audits after seed changes and the next bounded crawl.",
        ]
    return ["No new public topic candidates were found in stored snapshots; continue with eval and freshness gates."]


def _review_next_actions(status: str) -> list[str]:
    if status == "missing_run":
        return ["Create or restore a bounded crawl receipt before reviewing discovery candidates."]
    if status == "missing_review":
        return ["Create a discovery review manifest before changing seeds or claiming seed maturity."]
    if status == "invalid_review":
        return ["Fix the discovery review manifest schema, profile id, decisions, or rules."]
    if status == "needs_review":
        return ["Review remaining discovery candidates and record accept/reject/defer decisions in the manifest."]
    if status == "reviewed_pending_seed_update":
        return [
            "Apply accepted candidates to the profile seed file as bounded public seed windows.",
            "Run an operator-confirmed bounded crawl, then rebuild normalize/index/vector/graph artifacts.",
            "Re-run discovery review, coverage, refresh, and live quality gates against the refreshed run.",
        ]
    return ["Discovery candidates are reviewed and no accepted candidates are missing from seeds."]
