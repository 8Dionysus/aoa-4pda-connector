"""Post chunking helpers for local evidence search."""

from __future__ import annotations

import re
from collections.abc import Mapping


DEFAULT_MAX_CHARS = 900
DEFAULT_OVERLAP_CHARS = 160


def chunk_post(
    post: Mapping[str, object],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[dict[str, object]]:
    """Split one normalized post into deterministic evidence chunks."""

    text = _canonical_spaces(str(post.get("text", "")))
    if not text:
        return []
    topic_id = str(post.get("topic_id", "unknown-topic"))
    post_id = str(post.get("post_id", "unknown-post"))
    source_url = str(post.get("source_url", ""))
    windows = _chunk_windows(text, max_chars=max_chars, overlap_chars=overlap_chars)
    chunks: list[dict[str, object]] = []
    for index, (start, end) in enumerate(windows):
        chunk_text = text[start:end].strip()
        if not chunk_text:
            continue
        chunks.append(
            {
                "chunk_id": f"{topic_id}:{post_id}:chunk-{index:03d}",
                "topic_id": topic_id,
                "post_id": post_id,
                "source_url": source_url,
                "chunk_index": index,
                "char_start": start,
                "char_end": end,
                "text": chunk_text,
            }
        )
    return chunks


def _chunk_windows(text: str, *, max_chars: int, overlap_chars: int) -> list[tuple[int, int]]:
    if len(text) <= max_chars:
        return [(0, len(text))]
    windows: list[tuple[int, int]] = []
    start = 0
    while start < len(text):
        target_end = min(len(text), start + max_chars)
        end = _nearest_boundary(text, start, target_end)
        if end <= start:
            end = target_end
        windows.append((start, end))
        if end >= len(text):
            break
        next_start = end if end > 0 and text[end - 1] == "\n" else max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        start = _left_trim_to_word(text, next_start)
    return windows


def _nearest_boundary(text: str, start: int, target_end: int) -> int:
    if target_end >= len(text):
        return len(text)
    min_end = start + min(120, max(1, target_end - start))
    paragraph = text.find("\n\n", min_end, target_end)
    if paragraph > start:
        return paragraph + 2
    line = text.find("\n", min_end, target_end)
    if line > start:
        return line + 1
    floor = start + max(120, int((target_end - start) * 0.65))
    candidates = [text.rfind(boundary, floor, target_end) for boundary in [". ", "! ", "? ", "\n", "; "]]
    boundary = max(candidates)
    if boundary > start:
        return boundary + 1
    space = text.rfind(" ", floor, target_end)
    return space if space > start else target_end


def _left_trim_to_word(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def _canonical_spaces(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
