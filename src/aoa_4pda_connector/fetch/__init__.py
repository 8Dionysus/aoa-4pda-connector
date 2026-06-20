"""Bounded public-page fetch helpers."""

from __future__ import annotations

import hashlib
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from aoa_4pda_connector.policy import is_url_allowed


DEFAULT_USER_AGENT = "aoa-4pda-connector/0.1 starter-crawl (+local evidence connector)"


@dataclass(frozen=True)
class FetchResult:
    url: str
    path: Path
    bytes_written: int
    sha256: str
    status: int


def canonical_topic_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    showtopic = query.get("showtopic", [""])[0]
    st = query.get("st", ["0"])[0]
    canonical_query = urlencode({"showtopic": showtopic, "st": st})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", canonical_query, ""))


def topic_page_url(url: str, page_index: int, *, posts_per_page: int = 20) -> str:
    parsed = urlparse(canonical_topic_url(url))
    query = parse_qs(parsed.query)
    base_start = int(query.get("st", ["0"])[0] or 0)
    query["st"] = [str(base_start + page_index * posts_per_page)]
    canonical_query = urlencode({"showtopic": query.get("showtopic", [""])[0], "st": query["st"][0]})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", canonical_query, ""))


def topic_id_from_url(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    return query.get("showtopic", ["unknown"])[0]


def topic_page_start_from_url(url: str) -> str:
    query = parse_qs(urlparse(url).query)
    return query.get("st", ["0"])[0]


def fetch_public_topic(url: str, output_dir: Path, user_agent: str = DEFAULT_USER_AGENT) -> FetchResult:
    canonical = canonical_topic_url(url)
    if not is_url_allowed(canonical):
        raise ValueError(f"URL is outside public topic policy: {url}")
    topic_id = topic_id_from_url(canonical)
    page_start = topic_page_start_from_url(canonical)
    output_dir.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(canonical, headers={"User-Agent": user_agent, "Cookie": "deskver=1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        status = int(getattr(response, "status", 200))
    digest = hashlib.sha256(data).hexdigest()
    path = output_dir / f"topic-{topic_id}-st{page_start}-{digest[:12]}.html"
    path.write_bytes(data)
    return FetchResult(canonical, path, len(data), digest, status)


def polite_sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
