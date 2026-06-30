from __future__ import annotations

import json
from pathlib import Path

from aoa_4pda_connector.fetch import topic_page_start_from_url, topic_page_url
from aoa_4pda_connector.index import build_keyword_index, extract_exact_terms, technical_alias_tokens, tokenize
from aoa_4pda_connector.normalize import normalize_snapshot
from aoa_4pda_connector.parse import clean_text, decode_html, extract_posts, extract_title
from aoa_4pda_connector.query import _ranking_key, packet_id_for_query, query_keyword_index


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_parse_synthetic_topic_fixture():
    raw = (REPO_ROOT / "connector/fixtures/html/synthetic_topic.html").read_bytes()
    document = decode_html(raw)
    assert "Synthetic Redmi Note 10" in extract_title(document)
    posts = extract_posts(document)
    assert len(posts) == 2
    assert posts[1]["post_id"] == "1002"
    assert "bootloop" in posts[1]["text"]


def test_decode_html_prefers_valid_utf8_before_cp1251_fallback():
    document = decode_html("Xiaomi 13T на HyperOS".encode("utf-8"))

    assert "на HyperOS" in document
    assert "РЅР°" not in document


def test_parse_live_shape_fixture_extracts_metadata_and_drops_noise():
    raw = (REPO_ROOT / "connector/fixtures/html/live_shape_topic.html").read_bytes()
    document = decode_html(raw)
    posts = extract_posts(document)

    assert len(posts) == 1
    post = posts[0]
    assert post["post_id"] == "9001"
    assert post["author_label"] == "fixture_author"
    assert post["posted_at"] == "01.04.21, 09:32"
    assert "fastboot flash recovery recovery.img" in post["text"]
    assert "Restore boot.img" in post["text"]
    assert "Quoted stale boot.img" not in post["text"]
    assert "Edited by fixture moderator" not in post["text"]
    assert "--------------------" not in post["text"]
    assert "Signature mentions" not in post["text"]
    assert "profile card noise" not in post["text"]


def test_clean_text_keeps_post_text_after_void_tags_inside_ignored_block():
    fragment = (
        '<div class="post-block quote">quoted stale text<br><img src="noise.png"></div>'
        "<p>Real recovery text after quote.</p>"
    )

    assert clean_text(fragment) == "Real recovery text after quote."


def test_normalize_live_shape_fixture_preserves_post_metadata(tmp_path):
    raw_path = REPO_ROOT / "connector/fixtures/html/live_shape_topic.html"
    output_path = normalize_snapshot(
        raw_path,
        "https://4pda.to/forum/index.php?showtopic=42&st=0",
        tmp_path,
    )
    topic = json.loads(output_path.read_text(encoding="utf-8"))
    post = topic["posts"][0]

    assert output_path.name == "topic-42-st0.json"
    assert topic["page_start"] == "0"
    assert post["post_id"] == "9001"
    assert post["author_label"] == "fixture_author"
    assert post["posted_at"] == "01.04.21, 09:32"
    assert post["source_url"] == "https://4pda.to/forum/index.php?showtopic=42&st=0#entry9001"
    assert {"kind": "tool", "value": "TWRP"} in post["entities"]
    assert {"kind": "tool", "value": "fastboot"} in post["entities"]
    assert {"kind": "file", "value": "boot.img"} in post["entities"]


def test_topic_page_url_generates_public_pagination_offsets():
    seed = "https://4pda.to/forum/index.php?showtopic=42"

    assert topic_page_url(seed, 0) == "https://4pda.to/forum/index.php?showtopic=42&st=0"
    assert topic_page_url(seed, 1) == "https://4pda.to/forum/index.php?showtopic=42&st=20"
    assert topic_page_url(seed, 2) == "https://4pda.to/forum/index.php?showtopic=42&st=40"
    assert topic_page_start_from_url(topic_page_url(seed, 2)) == "40"


def test_topic_page_url_preserves_seed_start_offset():
    seed = "https://4pda.to/forum/index.php?showtopic=1076859&st=1800"

    assert topic_page_url(seed, 0) == "https://4pda.to/forum/index.php?showtopic=1076859&st=1800"
    assert topic_page_url(seed, 1) == "https://4pda.to/forum/index.php?showtopic=1076859&st=1820"
    assert topic_page_start_from_url(topic_page_url(seed, 1)) == "1820"


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


def test_post_level_index_keeps_post_only_evidence_refs(tmp_path):
    index_path = tmp_path / "keyword_index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema": "aoa_4pda_keyword_index_v1",
                "profile_id": "starter",
                "unit": "post",
                "doc_count": 1,
                "docs": [
                    {
                        "doc_id": "post-doc-1002",
                        "topic_id": "synthetic-topic-1",
                        "post_id": "1002",
                        "source_url": "https://4pda.to/forum/index.php?showtopic=1#entry1002",
                        "text": "bootloop recovery.img boot.img",
                        "search_text": "bootloop recovery.img boot.img",
                        "exact_text": "bootloop recovery.img boot.img",
                        "exact_terms": ["recovery.img", "boot.img"],
                        "tokens": 3,
                    }
                ],
                "inverted": {"bootloop": [{"doc_id": "post-doc-1002", "count": 1}]},
                "exact": {"boot.img": ["post-doc-1002"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    packet = query_keyword_index(index_path, "bootloop boot.img")

    top = packet["results"][0]
    assert packet["query_report"]["unit"] == "post"
    assert top["chunk_id"] is None
    assert top["evidence_refs"] == ["post:1002"]


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


def test_tokenization_adds_technical_aliases_for_split_forum_terms():
    text = "Redmi Note 10 Pro sweet boot img V 14 0 7 0 SM G991B"
    tokens = tokenize(text)
    exact_terms = extract_exact_terms(tokens)
    aliases = technical_alias_tokens(text)

    assert "boot.img" in aliases
    assert "v14.0.7.0" in aliases
    assert "sm-g991b" in aliases
    assert "sweet" in aliases
    assert "boot.img" in exact_terms
    assert "v14.0.7.0" in exact_terms
    assert "sm-g991b" in exact_terms
    assert "sweet" in tokens


def test_tokenization_adds_xiaomi_13t_device_aliases():
    text = "Xiaomi 13T 2306 EPN60G recovery img"
    tokens = tokenize(text)
    exact_terms = extract_exact_terms(tokens)
    aliases = technical_alias_tokens(text)

    assert "aristotle" in aliases
    assert "2306epn60g" in aliases
    assert "recovery.img" in aliases
    assert "aristotle" in tokens
    assert "2306epn60g" in exact_terms
    assert "recovery.img" in exact_terms


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


def test_query_prioritizes_specific_terms_over_topic_boilerplate(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "specific-ranking",
        "source_url": "https://4pda.to/forum/index.php?showtopic=42",
        "title": "Redmi Note 10 Pro - Firmware",
        "captured_at": "2026-06-18T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "3001",
                "topic_id": "specific-ranking",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry3001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "Redmi Note 10 Pro firmware overview. Redmi Note 10 Pro firmware archive.",
                "entities": [],
            },
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "3002",
                "topic_id": "specific-ranking",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry3002",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "If bootloop appears after flashing recovery, boot to TWRP and flash recovery.img again.",
                "entities": [],
            },
        ],
    }
    (normalized_dir / "topic-specific-ranking.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )

    index_path = build_keyword_index(normalized_dir, tmp_path / "index")
    packet = query_keyword_index(index_path, "bootloop recovery.img redmi note 10")

    assert "bootloop" in packet["query_report"]["specific_terms"]
    assert "recovery.img" in packet["query_report"]["specific_terms"]
    top = packet["results"][0]
    assert top["post_id"] == "3002"
    assert "bootloop" in top["matched_specific_terms"]
    assert "recovery.img" in top["matched_specific_terms"]


def test_ranking_key_keeps_total_score_primary_over_specific_term_count():
    rare_but_weak = {
        "bm25": 0.2,
        "exact": 0.0,
        "phrase": 0.0,
        "matched_terms": {"rare-token"},
        "matched_exact_terms": set(),
        "matched_phrases": set(),
    }
    stronger_score = {
        "bm25": 2.0,
        "exact": 1.0,
        "phrase": 0.0,
        "matched_terms": {"common-token"},
        "matched_exact_terms": {"common-token"},
        "matched_phrases": set(),
    }

    ranked = sorted(
        [("weak", rare_but_weak), ("strong", stronger_score)],
        key=lambda item: _ranking_key(item, ["rare-token"]),
        reverse=True,
    )

    assert ranked[0][0] == "strong"


def test_query_normalizes_split_file_version_and_codename_aliases(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "technical-normalization",
        "source_url": "https://4pda.to/forum/index.php?showtopic=42",
        "title": "Redmi Note 10 Pro - Firmware",
        "captured_at": "2026-06-18T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "4001",
                "topic_id": "technical-normalization",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry4001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "General sweet firmware index without an image file.",
                "entities": [],
            },
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "4002",
                "topic_id": "technical-normalization",
                "source_url": "https://4pda.to/forum/index.php?showtopic=42#entry4002",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-18T00:00:00Z",
                "text": "Patch boot.img from firmware V14.0.7.0 before flashing Magisk.",
                "entities": [],
            },
        ],
    }
    (normalized_dir / "topic-technical-normalization.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )

    index_path = build_keyword_index(normalized_dir, tmp_path / "index")
    packet = query_keyword_index(index_path, "sweet boot img V 14 0 7 0")

    assert "boot.img" in packet["query_report"]["technical_terms"]
    assert "v14.0.7.0" in packet["query_report"]["technical_terms"]
    assert "sweet" in packet["query_report"]["terms"]
    top = packet["results"][0]
    assert top["post_id"] == "4002"
    assert "boot.img" in top["matched_exact_terms"]
    assert "v14.0.7.0" in top["matched_exact_terms"]
    assert "boot.img" in top["matched_specific_terms"]


def test_query_normalizes_xiaomi_13t_name_and_split_model_alias(tmp_path):
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    topic = {
        "schema": "aoa_4pda_normalized_topic_v1",
        "topic_id": "xiaomi-13t-normalization",
        "source_url": "https://4pda.to/forum/index.php?showtopic=1076859",
        "title": "Xiaomi 13T - Firmware",
        "captured_at": "2026-06-20T00:00:00Z",
        "posts": [
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "5001",
                "topic_id": "xiaomi-13t-normalization",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859#entry5001",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-20T00:00:00Z",
                "text": "Aristotle firmware note for model 2306EPN60G with TWRP and boot.img patching.",
                "entities": [],
            },
            {
                "schema": "aoa_4pda_normalized_post_v1",
                "post_id": "5002",
                "topic_id": "xiaomi-13t-normalization",
                "source_url": "https://4pda.to/forum/index.php?showtopic=1076859#entry5002",
                "author_label": None,
                "posted_at": None,
                "captured_at": "2026-06-20T00:00:00Z",
                "text": "General Xiaomi 13T discussion without model-specific recovery files.",
                "entities": [],
            },
        ],
    }
    (normalized_dir / "topic-xiaomi-13t-normalization.json").write_text(
        json.dumps(topic, ensure_ascii=False), encoding="utf-8"
    )

    index_path = build_keyword_index(normalized_dir, tmp_path / "index", "xiaomi-13t")
    packet = query_keyword_index(index_path, "Xiaomi 13T 2306 EPN60G boot img")

    assert "aristotle" in packet["query_report"]["technical_terms"]
    assert "2306epn60g" in packet["query_report"]["technical_terms"]
    assert "boot.img" in packet["query_report"]["technical_terms"]
    top = packet["results"][0]
    assert top["post_id"] == "5001"
    assert "2306epn60g" in top["matched_exact_terms"]
    assert "boot.img" in top["matched_exact_terms"]
    assert "aristotle" in top["matched_specific_terms"]


def test_query_packet_id_is_stable_across_processes():
    query = "Redmi Note 10 Pro TWRP boot.img"
    assert packet_id_for_query(query) == packet_id_for_query(query)
    assert packet_id_for_query(query) == "query-1e51a44d7d241e63"
