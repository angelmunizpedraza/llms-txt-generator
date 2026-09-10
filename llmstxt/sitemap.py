"""Find the sitemaps and read the URLs out of them."""

from __future__ import annotations

from urllib.parse import urljoin
from xml.etree import ElementTree

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

CONVENTIONAL = ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml", "/wp-sitemap.xml")

MAX_INDEX_DEPTH = 2


def sitemaps_from_robots(robots_txt: str, base_url: str = "") -> list[str]:
    """Every `Sitemap:` line in a robots.txt, in the order it appears."""
    found: list[str] = []
    for line in (robots_txt or "").splitlines():
        if line.strip().lower().startswith("sitemap:"):
            value = line.split(":", 1)[1].strip()
            if value:
                found.append(urljoin(base_url, value) if base_url else value)
    return found


def parse_sitemap_xml(xml: str) -> tuple[str, list[tuple[str, str]]]:
    """Read one sitemap document.

    Returns ("index", [(child sitemap url, "")]) for a sitemap index, or
    ("urlset", [(page url, lastmod)]) for a normal sitemap. A document that
    does not parse returns an empty list rather than raising: one broken
    sitemap should never take the whole run down.
    """
    try:
        root = ElementTree.fromstring((xml or "").encode("utf-8"))
    except ElementTree.ParseError:
        return "invalid", []

    if root.tag.endswith("sitemapindex"):
        children = [
            (node.text.strip(), "")
            for node in root.findall("sm:sitemap/sm:loc", NS)
            if node is not None and node.text
        ]
        return "index", children

    entries: list[tuple[str, str]] = []
    for node in root.findall("sm:url", NS):
        loc = node.find("sm:loc", NS)
        lastmod = node.find("sm:lastmod", NS)
        if loc is not None and loc.text:
            entries.append((loc.text.strip(), (lastmod.text or "").strip() if lastmod is not None else ""))
    return "urlset", entries


def dedupe(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Drop repeated URLs, keeping the first occurrence and its lastmod."""
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for url, lastmod in entries:
        if url in seen:
            continue
        seen.add(url)
        unique.append((url, lastmod))
    return unique


def collect(start_urls: list[str], read, depth: int = 0) -> list[tuple[str, str]]:
    """Walk sitemaps and indexes with `read(url) -> str | None`, breadth first.

    `read` is injected so the walk can be tested without a network, and so the
    caller decides about timeouts, user agents and politeness.
    """
    if depth > MAX_INDEX_DEPTH:
        return []

    out: list[tuple[str, str]] = []
    for url in start_urls:
        xml = read(url)
        if not xml:
            continue
        kind, entries = parse_sitemap_xml(xml)
        if kind == "index":
            out.extend(collect([u for u, _ in entries], read, depth + 1))
        else:
            out.extend(entries)
    return dedupe(out)
