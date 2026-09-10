from llmstxt.sitemap import collect, dedupe, parse_sitemap_xml, sitemaps_from_robots
from tests.conftest import ROBOTS, SITEMAP_INDEX, SITEMAP_PAGES


def test_robots_sitemap_lines_are_read_and_made_absolute():
    found = sitemaps_from_robots(ROBOTS, "https://example.com")
    assert found == ["https://example.com/sitemap.xml", "https://example.com/sitemap-extra.xml"]


def test_robots_without_sitemaps_returns_nothing():
    assert sitemaps_from_robots("User-agent: *\nDisallow:\n") == []


def test_a_sitemap_index_is_recognised():
    kind, entries = parse_sitemap_xml(SITEMAP_INDEX)
    assert kind == "index"
    assert [u for u, _ in entries] == [
        "https://example.com/sitemap-pages.xml",
        "https://example.com/sitemap-posts.xml",
    ]


def test_a_urlset_returns_urls_with_lastmod():
    kind, entries = parse_sitemap_xml(SITEMAP_PAGES)
    assert kind == "urlset"
    assert entries[0] == ("https://example.com/", "2026-09-01")
    assert entries[1][1] == ""


def test_a_broken_sitemap_does_not_raise():
    kind, entries = parse_sitemap_xml("<urlset><url><loc>oops")
    assert kind == "invalid"
    assert entries == []


def test_dedupe_keeps_the_first_occurrence():
    assert dedupe([("a", "1"), ("a", "2"), ("b", "")]) == [("a", "1"), ("b", "")]


def test_collect_follows_an_index_and_dedupes_across_children(reader):
    entries = collect(["https://example.com/sitemap.xml"], reader.get)
    urls = [u for u, _ in entries]
    assert urls.count("https://example.com/servicios") == 1
    assert "https://example.com/blog/primer-post" in urls


def test_collect_stops_at_the_depth_limit():
    # A sitemap index that points at itself would recurse forever.
    loop = (
        '<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        "<sitemap><loc>https://e.com/s.xml</loc></sitemap></sitemapindex>"
    )
    calls = {"n": 0}

    def read(_url):
        calls["n"] += 1
        return loop

    assert collect(["https://e.com/s.xml"], read) == []
    assert calls["n"] < 10
