from llmstxt.analyse import build_profile, discover_sitemaps, page_metadata


def test_sitemaps_come_from_robots_first(reader):
    found = discover_sitemaps("https://example.com", reader)
    assert found[0] == "https://example.com/sitemap.xml"


def test_metadata_falls_back_to_the_h1_when_there_is_no_description():
    meta = page_metadata("<html><head><title>Servicios</title></head><body><h1>Cirugía</h1></body></html>")
    assert meta["title"] == "Servicios"
    assert meta["description"] == "Cirugía"


def test_noindex_is_detected():
    assert page_metadata('<meta name="robots" content="NOINDEX, follow">')["noindex"] is True
    assert page_metadata("<html></html>")["noindex"] is False


def test_noindex_pages_are_dropped_by_default(reader):
    profile = build_profile("https://example.com", reader)
    assert all("aviso-legal" not in p.url for p in profile.pages)


def test_noindex_pages_can_be_kept(reader):
    profile = build_profile("https://example.com", reader, skip_noindex=False)
    assert any("aviso-legal" in p.url for p in profile.pages)


def test_site_name_comes_from_the_home_title_before_the_separator(reader):
    profile = build_profile("https://example.com", reader)
    assert profile.site_name == "Clínica Ejemplo"
    assert "braquicéfalas" in profile.summary


def test_max_urls_is_respected(reader):
    assert len(build_profile("https://example.com", reader, max_urls=2).pages) <= 2


def test_include_and_exclude_filter_urls(reader):
    only_blog = build_profile("https://example.com", reader, include=r"/blog/")
    assert [p.url for p in only_blog.pages] == ["https://example.com/blog/primer-post"]

    no_blog = build_profile("https://example.com", reader, exclude=r"/blog/")
    assert all("/blog/" not in p.url for p in no_blog.pages)


def test_pages_are_classified(reader):
    profile = build_profile("https://example.com", reader)
    by_url = {p.url: p.section for p in profile.pages}
    assert by_url["https://example.com/"] == "Home"
    assert by_url["https://example.com/servicios"] == "Servicios"
    assert by_url["https://example.com/blog/primer-post"] == "Contenido y guías"
