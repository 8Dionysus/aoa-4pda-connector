from __future__ import annotations

import json

from aoa_4pda_connector.chunk import chunk_post
from aoa_4pda_connector.index import build_keyword_index
from aoa_4pda_connector.query import query_keyword_index


def _long_post_text() -> str:
    opening = " ".join(["opening noise firmware chatter"] * 80)
    middle = (
        "Target instruction: connect phone in fastboot mode, then run "
        "fastboot flash recovery recovery.img and fastboot boot recovery.img. "
        "If bootloop appears, restore boot.img from the same firmware package."
    )
    tail = " ".join(["tail discussion unrelated battery theme"] * 80)
    return f"{opening}\n\n{middle}\n\n{tail}"


def test_chunk_post_preserves_source_refs_and_overlaps_long_text():
    post = {
        "topic_id": "chunk-topic",
        "post_id": "3001",
        "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry3001",
        "text": _long_post_text(),
    }

    chunks = chunk_post(post, max_chars=520, overlap_chars=90)

    assert len(chunks) > 1
    assert chunks[0]["chunk_id"] == "chunk-topic:3001:chunk-000"
    assert all(chunk["topic_id"] == "chunk-topic" for chunk in chunks)
    assert all(chunk["post_id"] == "3001" for chunk in chunks)
    assert all(chunk["source_url"].endswith("#entry3001") for chunk in chunks)
    assert all(len(chunk["text"]) <= 620 for chunk in chunks)
    assert any("fastboot flash recovery recovery.img" in chunk["text"] for chunk in chunks)
    assert chunks[1]["char_start"] < chunks[0]["char_end"]


def test_chunk_offsets_slice_source_text_before_space_canonicalization():
    source_text = "  alpha\t\tbeta   gamma\n\n\n\ndelta  "
    post = {
        "topic_id": "chunk-topic",
        "post_id": "3002",
        "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry3002",
        "text": source_text,
    }

    chunk = chunk_post(post, max_chars=200, overlap_chars=20)[0]
    source_slice = source_text[chunk["char_start"] : chunk["char_end"]]

    assert chunk["text"] == "alpha beta gamma\n\ndelta"
    assert "alpha\t\tbeta" in source_slice
    assert source_slice.strip().startswith("alpha")
    assert source_slice.strip().endswith("delta")


def test_keyword_index_queries_return_precise_chunk_evidence(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "chunk-topic",
        "source_url": "https://4pda.to/forum/index.php?showtopic=42",
        "title": "Redmi Note 10 Pro - TWRP",
        "captured_at": "2026-06-18T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "3001",
                "topic_id": "chunk-topic",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry3001",
                "author_label": "fixture_author",
                "posted_at": "01.04.21, 09:32",
                "captured_at": "2026-06-18T00:00:00Z",
                "text": _long_post_text(),
                "entities": [],
            }
        ],
    }
    (normalized_dir / "topic-chunk-topic.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )

    index_path = build_keyword_index(normalized_dir, tmp_path / "index")
    packet = query_keyword_index(index_path, "fastboot flash recovery recovery.img boot.img")

    assert packet["query_report"]["unit"] == "chunk"
    top = packet["results"][0]
    assert top["post_id"] == "3001"
    assert top["chunk_id"].startswith("chunk-topic:3001:chunk-")
    assert top["chunk_index"] >= 0
    assert top["evidence_refs"][0].startswith("chunk:")
    assert "fastboot flash recovery recovery.img" in top["snippet"]
    assert "opening noise" not in top["snippet"]
