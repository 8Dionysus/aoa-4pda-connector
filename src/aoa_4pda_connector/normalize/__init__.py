"""Normalize raw public topic snapshots into JSON records."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from aoa_4pda_connector.fetch import topic_id_from_url, topic_page_start_from_url
from aoa_4pda_connector.parse import decode_html, extract_posts, extract_title


FILE_RE = re.compile(r"\b[\w.-]+\.(?:img|zip|apk|bin|tar|tgz|xz)\b", re.I)
FIRMWARE_VERSION_RE = re.compile(r"\bV\d+(?:\.\d+){2,}(?:\.[A-Z0-9]+)?\b", re.I)
BUILD_ID_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9]{2,}(?:\.[A-Z0-9]+){2,}\b")
DEVICE_RE = re.compile(
    r"\b(?:Redmi\s+Note\s+\d+(?:\s+Pro|\s+Plus)?|Redmi\s+\d+[A-Za-z]*|Xiaomi\s+Mi\s+Pad\s+\d(?:\s+Plus)?|Poco\s+[A-Z0-9 ]{2,12})\b",
    re.I,
)
KNOWN_TOOLS = {
    "adb": "ADB",
    "fastboot": "fastboot",
    "magisk": "Magisk",
    "miflash": "MiFlash",
    "twrp": "TWRP",
}
KNOWN_CODENAMES = {
    "camellia",
    "clover",
    "mojito",
    "sweet",
    "sunny",
}
FIRMWARE_FAMILIES = {
    "miui": "MIUI",
    "hyperos": "HyperOS",
}
ISSUE_TERMS = {
    "bootloop": "bootloop",
    "бутлуп": "bootloop",
    "кирпич": "brick",
    "brick": "brick",
}


def normalize_snapshot(raw_path: Path, source_url: str, output_dir: Path) -> Path:
    document = decode_html(raw_path.read_bytes())
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    topic_id = topic_id_from_url(source_url)
    page_start = topic_page_start_from_url(source_url)
    posts = []
    for post in extract_posts(document):
        post_id = post["post_id"]
        posts.append(
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": post_id,
                "topic_id": topic_id,
                "source_url": f"{source_url}#entry{post_id}",
                "author_label": post.get("author_label"),
                "posted_at": post.get("posted_at"),
                "captured_at": captured_at,
                "text": post["text"],
                "entities": extract_entities(post["text"]),
            }
        )
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": topic_id,
        "page_start": page_start,
        "source_url": source_url,
        "title": extract_title(document),
        "captured_at": captured_at,
        "posts": posts,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"topic-{topic_id}-st{page_start}.json"
    output_path.write_text(json.dumps(topic, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def extract_entities(text: str) -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    lowered = text.lower()
    for match in DEVICE_RE.finditer(text):
        _add_entity(entities, "device", _canonical_spaces(match.group(0)))
    for match in FIRMWARE_VERSION_RE.finditer(text):
        _add_entity(entities, "firmware_version", match.group(0).upper())
    for match in BUILD_ID_RE.finditer(text):
        _add_entity(entities, "build_id", match.group(0).upper())
    for raw, canonical in FIRMWARE_FAMILIES.items():
        if re.search(rf"\b{re.escape(raw)}\b", lowered):
            _add_entity(entities, "firmware_family", canonical)
    for raw, canonical in KNOWN_TOOLS.items():
        if re.search(rf"\b{re.escape(raw)}\b", lowered):
            _add_entity(entities, "tool", canonical)
    for codename in KNOWN_CODENAMES:
        if re.search(rf"\b{re.escape(codename)}\b", lowered):
            _add_entity(entities, "codename", codename)
    for match in FILE_RE.finditer(text):
        _add_entity(entities, "file", match.group(0).lower())
    for raw, canonical in ISSUE_TERMS.items():
        if re.search(rf"\b{re.escape(raw)}\b", lowered):
            _add_entity(entities, "issue", canonical)

    for file_entity in [entity for entity in entities if entity["kind"] == "file"]:
        file_value = file_entity["value"]
        if re.search(rf"\b(?:restore|восстанов(?:ить|и|ление)|верн(?:уть|и))\b[^.?!]{{0,80}}{re.escape(file_value)}", lowered):
            _add_entity(entities, "fix", f"restore {file_value}")
        if re.search(rf"\b(?:flash|прош(?:ить|ей|ивка))\b[^.?!]{{0,80}}{re.escape(file_value)}", lowered):
            _add_entity(entities, "fix", f"flash {file_value}")

    for file_entity in [entity for entity in entities if entity["kind"] == "file"]:
        for codename_entity in [entity for entity in entities if entity["kind"] == "codename"]:
            warning = _canonical_warning(lowered, file_entity["value"], codename_entity["value"])
            if warning:
                _add_entity(entities, "warning", warning)
    return entities


def _add_entity(entities: list[dict[str, str]], kind: str, value: str) -> None:
    canonical = _canonical_spaces(value)
    if not canonical:
        return
    if any(entity["kind"] == kind and entity["value"].casefold() == canonical.casefold() for entity in entities):
        return
    entities.append({"kind": kind, "value": canonical})


def _canonical_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _canonical_warning(lowered_text: str, file_value: str, codename: str) -> str | None:
    file_pattern = re.escape(file_value)
    codename_pattern = re.escape(codename)
    has_warning_marker = "warning" in lowered_text or "важно" in lowered_text or "не ставить" in lowered_text
    if not has_warning_marker:
        return None
    if re.search(rf"(?:не\s+ставить|do\s+not\s+install|warning).{{0,160}}{file_pattern}.{{0,80}}(?:от|from)\s+{codename_pattern}", lowered_text):
        return f"do not install {file_value} from {codename}"
    return None
