"""Put the pieces together: from a base URL to a SiteProfile."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from .classify import classify, clean_text
from .model import Page, SiteProfile
from .sitemap import CONVENTIONAL, collect, sitemaps_from_robots

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.IGNORECASE)


def discover_sitemaps(base_url: str, reader) -> list[str]:
    """Sitemaps declared in robots.txt, plus the conventional paths that exist."""
    found = sitemaps_from_robots(reader.get(urljoin(base_url, "/robots.txt")) or "", base_url)
    for candidate in CONVENTIONAL:
        url = urljoin(base_url, candidate)
        if url not in found and reader.exists(url):
            found.append(url)
    return found


def page_metadata(html: str) -> dict:
    """Title, description and noindex from one HTML document."""
    title = TITLE_RE.search(html or "")
    desc = DESC_RE.search(html or "")
    h1 = H1_RE.search(html or "")
    return {
        "title": clean_text(title.group(1), 90) if title else "",
        "description": clean_text(desc.group(1), 160) if desc else (clean_text(h1.group(1), 160) if h1 else ""),
        "noindex": bool(NOINDEX_RE.search(html or "")),
    }


def build_profile(base_url: str, reader, max_urls: int = 100, skip_noindex: bool = True,
                  include: str = "", exclude: str = "") -> SiteProfile:
    profile = SiteProfile(domain=urlparse(base_url).netloc)

    sitemaps = discover_sitemaps(base_url, reader)
    if sitemaps:
        entries = collect(sitemaps, reader.get)
    else:
        entries = [(base_url, "")]

    inc = re.compile(include) if include else None
    exc = re.compile(exclude) if exclude else None

    selected: list[tuple[str, str]] = []
    for url, lastmod in entries:
        if inc and not inc.search(url):
            continue
        if exc and exc.search(url):
            continue
        selected.append((url, lastmod))
        if len(selected) >= max_urls:
            break

    for url, lastmod in selected:
        page = Page(url=url, lastmod=lastmod)
        page.section = classify(page.path)
        html = reader.get(url)
        if html:
            meta = page_metadata(html)
            if meta["noindex"] and skip_noindex:
                continue
            page.title = meta["title"]
            page.description = meta["description"]
        profile.pages.append(page)

    for page in profile.pages:
        if page.is_home:
            profile.site_name = re.split(r"[|\-–—]", page.title)[0].strip() or profile.domain
            profile.summary = page.description
            break
    if not profile.site_name:
        profile.site_name = profile.domain

    return profile
