"""Pull http(s) links out of HTML + visible text so the model only ever indexes real URLs."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

_DATA_HINT_RE = re.compile(
    r"\.(?:csv|json|jsonl|parquet|zip|gz|tgz|tar|tsv|sqlite|db)(?:\?|$)|"
    r"(?:download|dataset|dump|api|blob|raw)",
    re.I,
)


def normalize_http_url(base_url: str, link: str | None) -> str | None:
    if not link or not isinstance(link, str):
        return None
    link = link.strip()
    if link.startswith("#") or link.lower().startswith("javascript:"):
        return None
    try:
        abs_url = urljoin(base_url, link)
    except ValueError:
        return None
    p = urlparse(abs_url)
    if p.scheme not in ("http", "https") or not p.netloc:
        return None
    netloc = p.netloc.lower()
    path = p.path or "/"
    cleaned = urlunparse((p.scheme.lower(), netloc, path, "", p.query, ""))
    return cleaned


def normalize_page_url(url: str) -> str:
    """Cheap fingerprint so we don't save the same page twice."""
    p = urlparse(url.strip())
    netloc = p.netloc.lower()
    path = (p.path or "/").rstrip("/") or "/"
    return urlunparse((p.scheme.lower(), netloc, path, "", p.query, ""))


_TEXT_URL_RE = re.compile(r"https?://[^\s\"'<>)\]}]+", re.I)


def harvest_urls(page_url: str, raw_html: str | None, text: str | None, max_urls: int) -> list[str]:
    """Dedupe, bump file-ish URLs toward the front of the list."""
    seen: dict[str, None] = {}
    out: list[str] = []

    def remember(u: str | None) -> None:
        if not u or u in seen:
            return
        seen[u] = None
        out.append(u)

    if raw_html:
        try:
            soup = BeautifulSoup(raw_html, "lxml")
            for tag in soup.find_all(["a", "link", "script", "img", "source", "iframe"]):
                href = tag.get("href") or tag.get("src")
                remember(normalize_http_url(page_url, href))
        except Exception:
            pass

    plain = text or ""
    for m in _TEXT_URL_RE.finditer(plain):
        remember(normalize_http_url(page_url, m.group(0)))

    def sort_key(u: str) -> tuple[int, str]:
        low = u.lower()
        bump = 2 if _DATA_HINT_RE.search(low) else 0
        return (-bump, u)

    out.sort(key=sort_key)
    cap = max_urls if max_urls > 0 else 120
    return out[:cap]
