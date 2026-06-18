from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.index import build_keyword_index, extract_exact_terms, tokenize
from aoa_4pda_connector.parse import decode_html, extract_posts, extract_title
from aoa_4pda_connector.query import query_keyword_index


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_parse_synthetic_topic_fixture():
    raw = (REPO_ROOT / "connector/fixtures/html/synthetic_topic.html").read_bytes()
    document = decode_html(raw)
    assert "Synthetic Redmi Note 10" in extract_title(document)
    posts = extract_posts(document)
    assert len(posts) == 2
    assert posts[1]["post_id"] == "1002"
    assert "bootloop" in posts[1]["text"]


def test_keyword_index_and_query_fixture(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    source = json.loads(
        (REPO_ROOT / "connector/fixtures/normalized/synthetic_topic.json").read_text(encoding="utf-8")
    )
    (normalized_dir / "topic-synthetic-topic-1.json").write_text(
        json.dumps(source, ensure_ascii=False), encoding="utf-8"
    )
    index_path = build_keyword_index(normalized_dir, tmp_path / "index")
    packet = query_keyword_index(index_path, "bootloop boot.img")
    assert packet["policy"]["internal_search_used"] is False
    assert packet["results"][0]["post_id"] == "1002"


def test_tokenization_preserves_forum_search_terms():
    text = "Redmi Note 10 Pro boot.img V14.0.7.0 бутлуп recovery.img"
    tokens = tokenize(text)
    exact_terms = extract_exact_terms(tokens)
    assert "redmi" in tokens
    assert "бутлуп" in tokens
    assert "boot.img" in tokens
    assert "v14.0.7.0" in exact_terms
    assert "recovery.img" in exact_terms
    assert "10" in exact_terms


def test_query_uses_bm25_exact_terms_phrases_and_focused_snippets(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "search-quality",
        "source_url": "https://4pda.to/forum/index.php?showtopic=42",
        "title": "Redmi Note 10 Pro - Firmware",
        "captured_at": "2026-06-18T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "2001",
                "topic_id": "search-quality",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry2001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "Short firmware note with firmware firmware firmware.",
                "entities": [],
            },
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "2002",
                "topic_id": "search-quality",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry2002",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "After flashing V14.0.7.0 the phone hits bootloop. Restore boot.img from the Redmi Note 10 Pro firmware.",
                "entities": [],
            },
        ],
    }
    (normalized_dir / "topic-search-quality.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )

    index_path = build_keyword_index(normalized_dir, tmp_path / "index")
    packet = query_keyword_index(index_path, "Redmi Note 10 Pro bootloop boot.img V14.0.7.0")

    assert packet["query_report"]["algorithm"] == "bm25_exact_v1"
    assert packet["query_report"]["terms"][:4] == ["redmi", "note", "10", "pro"]
    assert "boot.img" in packet["query_report"]["exact_terms"]
    assert "redmi note 10 pro" in packet["query_report"]["phrase_candidates"]
    top = packet["results"][0]
    assert top["post_id"] == "2002"
    assert "boot.img" in top["matched_exact_terms"]
    assert "redmi note 10 pro" in top["matched_phrases"]
    assert top["score_breakdown"]["bm25"] > 0
    assert top["score_breakdown"]["exact"] > 0
    assert top["score_breakdown"]["phrase"] > 0
    assert "boot.img" in top["snippet"]
