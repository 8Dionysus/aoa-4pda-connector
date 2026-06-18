"""Small URL policy helpers for the skeleton.

These helpers intentionally enforce only the stable skeleton boundary. Future
network code should still parse robots and operator policy before fetching.
"""

from __future__ import annotations

from urllib.parse import urlparse


ALLOWED_HOSTS = {"4pda.to", "4pda.ru"}
ALLOWED_PATH_PREFIX = "/forum/index.php"
ALLOWED_QUERY_TOKEN = "showtopic="

DENIED_TOKENS = {
    "act=search",
    "act=Search",
    "act=findpost",
    "act=attach",
    "act=login",
    "act=Login",
    "act=auth",
    "act=usercp",
    "act=post",
    "act=Post",
    "act=report",
    "act=warn",
    "/forum/dl",
    "/forum/lofiversion/",
}


def is_url_allowed(url: str) -> bool:
    """Return True when *url* matches the current public-topic skeleton route."""

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc not in ALLOWED_HOSTS:
        return False
    joined = f"{parsed.path}?{parsed.query}"
    if any(token in joined for token in DENIED_TOKENS):
        return False
    return parsed.path == ALLOWED_PATH_PREFIX and ALLOWED_QUERY_TOKEN in parsed.query

