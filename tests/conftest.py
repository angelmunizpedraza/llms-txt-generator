import pytest

from llmstxt.model import Page, SiteProfile

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap-posts.xml</loc></sitemap>
</sitemapindex>
"""

SITEMAP_PAGES = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc><lastmod>2026-09-01</lastmod></url>
  <url><loc>https://example.com/servicios</loc></url>
  <url><loc>https://example.com/contacto</loc></url>
  <url><loc>https://example.com/aviso-legal</loc></url>
</urlset>
"""

SITEMAP_POSTS = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/blog/primer-post</loc><lastmod>2026-08-20</lastmod></url>
  <url><loc>https://example.com/servicios</loc></url>
</urlset>
"""

ROBOTS = """User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
sitemap: /sitemap-extra.xml
"""

HTML = {
    "https://example.com/": (
        "<html><head><title>Clínica Ejemplo | Veterinaria en Sevilla</title>"
        '<meta name="description" content="Clínica veterinaria en Sevilla especializada en razas braquicéfalas.">'
        "</head><body><h1>Clínica Ejemplo</h1></body></html>"
    ),
    "https://example.com/servicios": (
        "<html><head><title>Servicios</title></head><body><h1>Cirugía, diagnóstico y urgencias</h1></body></html>"
    ),
    "https://example.com/contacto": "<html><head><title>Contacto</title></head><body></body></html>",
    "https://example.com/aviso-legal": (
        '<html><head><title>Aviso legal</title><meta name="robots" content="noindex,follow">'
        "</head><body></body></html>"
    ),
    "https://example.com/blog/primer-post": (
        "<html><head><title>Cómo respira un bulldog</title>"
        '<meta name="description" content="Qué es el síndrome braquicéfalo y cuándo operar.">'
        "</head><body></body></html>"
    ),
}


class FakeReader:
    """Stands in for llmstxt.fetch.Reader without touching the network."""

    def __init__(self, pages=None, robots=ROBOTS, existing=("https://example.com/sitemap.xml",)):
        self.pages = dict(pages if pages is not None else HTML)
        self.pages["https://example.com/robots.txt"] = robots
        self.pages["https://example.com/sitemap.xml"] = SITEMAP_INDEX
        self.pages["https://example.com/sitemap-pages.xml"] = SITEMAP_PAGES
        self.pages["https://example.com/sitemap-posts.xml"] = SITEMAP_POSTS
        self.existing = set(existing)
        self.requested = []

    def get(self, url):
        self.requested.append(url)
        return self.pages.get(url)

    def exists(self, url):
        return url in self.existing

    def status(self, url):
        return 200 if url in self.pages else 404


@pytest.fixture()
def reader():
    return FakeReader()


@pytest.fixture()
def profile():
    p = SiteProfile(domain="example.com", site_name="Clínica Ejemplo", summary="Veterinaria en Sevilla.")
    p.pages = [
        Page("https://example.com/", "Clínica Ejemplo", "Veterinaria en Sevilla.", "Home"),
        Page("https://example.com/servicios", "Servicios", "Cirugía y diagnóstico.", "Servicios"),
        Page("https://example.com/blog/primer-post", "Cómo respira un bulldog", "", "Contenido y guías"),
    ]
    return p
