from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.index import build_keyword_index
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
