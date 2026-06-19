"""Small HTML parsing helpers for public topic snapshots."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser


H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
POST_ID_RE = re.compile(r'id=["\']post-main-(\d+)["\']', re.I)
TABLE_POST_RE = re.compile(
    r'<table[^>]+data-post=["\'](\d+)["\'][^>]*>(.*?)(?=<table[^>]+data-post=["\']\d+["\']|</body>|</html>|\Z)',
    re.I | re.S,
)
ARTICLE_POST_RE = re.compile(r'<article[^>]+id=["\']post-(\d+)["\'][^>]*>(.*?)</article>', re.I | re.S)
POST_BODY_RE = re.compile(
    r'<div[^>]+class=["\'][^"\']*post_body[^"\']*["\'][^>]*[^>]*id=["\']post-main-(\d+)["\'][^>]*>(.*?)</div>\s*</div>',
    re.I | re.S,
)
IGNORED_CLASS_TOKENS = {"edit", "post-edit-reason", "signature"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {key.lower(): value or "" for key, value in attrs}
        class_attr = attrs_map.get("class", "").lower()
        if self.skip_depth or tag.lower() in {"script", "style"} or _class_is_ignored(class_attr):
            self.skip_depth += 1

    def handle_endtag(self, _tag: str) -> None:
        if self.skip_depth:
            self.skip_depth -= 1

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


def extract_posts(document: str) -> list[dict[str, str | None]]:
    posts: list[dict[str, str | None]] = []
    for post_id, block in TABLE_POST_RE.findall(document):
        text = _extract_table_post_text(block, post_id)
        if text:
            posts.append(
                {
                    "post_id": post_id,
                    "author_label": _extract_table_author(block, post_id),
                    "posted_at": _extract_table_posted_at(block, post_id),
                    "text": text,
                }
            )
    if posts:
        return posts

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
    text = re.sub(r"-{10,}", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _class_is_ignored(class_attr: str) -> bool:
    classes = set(class_attr.split())
    if {"post-block", "quote"}.issubset(classes):
        return True
    return bool(classes.intersection(IGNORED_CLASS_TOKENS))


def _extract_table_post_text(block: str, post_id: str) -> str:
    match = re.search(
        rf'id=["\']post-main-{re.escape(post_id)}["\'][^>]*>(.*?)(?=</td>\s*</tr>\s*<tr[^>]+id=["\']pb-{re.escape(post_id)}-r3["\']|</table>)',
        block,
        re.I | re.S,
    )
    if not match:
        return ""
    return clean_text(match.group(1))[:8000]


def _extract_table_author(block: str, post_id: str) -> str | None:
    match = re.search(
        rf'id=["\']post-member-{re.escape(post_id)}["\'][^>]*>.*?<span[^>]+class=["\'][^"\']*normalname[^"\']*["\'][^>]*>\s*<a[^>]*>(.*?)</a>',
        block,
        re.I | re.S,
    )
    return clean_text(match.group(1)) if match else None


def _extract_table_posted_at(block: str, post_id: str) -> str | None:
    match = re.search(
        rf'id=["\']ph-{re.escape(post_id)}-d2["\'][^>]*>.*?</div>\s*<img[^>]*>\s*([^<]+?)\s*<span[^>]+id=["\']kh-{re.escape(post_id)}["\']',
        block,
        re.I | re.S,
    )
    return clean_text(match.group(1)) if match else None
