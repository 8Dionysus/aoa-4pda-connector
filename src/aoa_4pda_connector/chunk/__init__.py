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

    source_text = str(post.get("text", ""))
    text, source_spans = _canonical_spaces_with_source_spans(source_text)
    if not text:
        return []
    topic_id = str(post.get("topic_id", "unknown-topic"))
    post_id = str(post.get("post_id", "unknown-post"))
    source_url = str(post.get("source_url", ""))
    windows = _chunk_windows(text, max_chars=max_chars, overlap_chars=overlap_chars)
    chunks: list[dict[str, object]] = []
    for index, (start, end) in enumerate(windows):
        chunk_start = start
        chunk_end = end
        while chunk_start < chunk_end and text[chunk_start].isspace():
            chunk_start += 1
        while chunk_end > chunk_start and text[chunk_end - 1].isspace():
            chunk_end -= 1
        chunk_text = text[chunk_start:chunk_end]
        if not chunk_text:
            continue
        source_start = source_spans[chunk_start][0]
        source_end = source_spans[chunk_end - 1][1]
        chunks.append(
            {
                "chunk_id": f"{topic_id}:{post_id}:chunk-{index:03d}",
                "topic_id": topic_id,
                "post_id": post_id,
                "source_url": source_url,
                "posted_at": post.get("posted_at"),
                "captured_at": post.get("captured_at"),
                "chunk_index": index,
                "char_start": source_start,
                "char_end": source_end,
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


def _canonical_spaces_with_source_spans(text: str) -> tuple[str, list[tuple[int, int]]]:
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in " \t\f\v":
            start = index
            while index < len(text) and text[index] in " \t\f\v":
                index += 1
            chars.append(" ")
            spans.append((start, index))
            continue
        if char in "\r\n":
            newline_spans: list[tuple[int, int]] = []
            while index < len(text) and text[index] in "\r\n":
                start = index
                if text[index] == "\r" and index + 1 < len(text) and text[index + 1] == "\n":
                    index += 2
                else:
                    index += 1
                newline_spans.append((start, index))
            kept = newline_spans[:2]
            if len(newline_spans) > 2:
                kept[-1] = (kept[-1][0], newline_spans[-1][1])
            for start, end in kept:
                chars.append("\n")
                spans.append((start, end))
            continue
        chars.append(char)
        spans.append((index, index + 1))
        index += 1

    start = 0
    end = len(chars)
    while start < end and chars[start].isspace():
        start += 1
    while end > start and chars[end - 1].isspace():
        end -= 1
    return "".join(chars[start:end]), spans[start:end]
