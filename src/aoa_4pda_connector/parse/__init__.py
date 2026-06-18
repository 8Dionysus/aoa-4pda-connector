"""Small HTML parsing helpers for public topic snapshots."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser


H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
POST_ID_RE = re.compile(r'id=["\']post-main-(\d+)["\']', re.I)
ARTICLE_POST_RE = re.compile(r'<article[^>]+id=["\']post-(\d+)["\'][^>]*>(.*?)</article>', re.I | re.S)
POST_BODY_RE = re.compile(
    r'<div[^>]+class=["\'][^"\']*post_body[^"\']*["\'][^>]*[^>]*id=["\']post-main-(\d+)["\'][^>]*>(.*?)</div>\s*</div>',
    re.I | re.S,
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return " ".join(self.parts)


def decode_html(data: bytes) -> str:
    for encoding in ["windows-1251", "utf-8"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("windows-1251", errors="replace")


def extract_title(document: str) -> str:
    h1_match = H1_RE.search(document)
    if h1_match:
        return clean_text(h1_match.group(1))
    match = TITLE_RE.search(document)
    if not match:
        return "Untitled 4PDA topic"
    return clean_text(match.group(1))


def extract_posts(document: str) -> list[dict[str, str]]:
    posts: list[dict[str, str]] = []
    for post_id, body in POST_BODY_RE.findall(document):
        text = clean_text(body)
        if text:
            posts.append({"post_id": post_id, "text": text})
    if posts:
        return posts

    for post_id, body in ARTICLE_POST_RE.findall(document):
        text = clean_text(body)
        if text:
            posts.append({"post_id": post_id, "text": text})
    if posts:
        return posts

    # Fallback: split by discovered post ids and keep a bounded text window.
    ids = list(POST_ID_RE.finditer(document))
    for index, match in enumerate(ids):
        start = match.end()
        end = ids[index + 1].start() if index + 1 < len(ids) else min(len(document), start + 12000)
        text = clean_text(document[start:end])
        if text:
            posts.append({"post_id": match.group(1), "text": text[:8000]})
    return posts


def clean_text(fragment: str) -> str:
    extractor = TextExtractor()
    extractor.feed(fragment)
    text = html.unescape(extractor.get_text())
    return re.sub(r"\s+", " ", text).strip()
