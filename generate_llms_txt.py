#!/usr/bin/env python3
"""
llms-txt-generator
==================
Genera un fichero llms.txt a partir del sitemap de un sitio web, para que los
modelos de lenguaje (ChatGPT, Claude, Perplexity, Google AI Overviews) puedan
descubrir y priorizar el contenido relevante.

El estandar llms.txt propone un fichero en la raiz del dominio que actua como
"robots.txt para LLMs": en lugar de bloquear rastreadores, orienta a los
modelos sobre que contenido importa y como esta organizado.

Uso:
    python generate_llms_txt.py https://ejemplo.com
    python generate_llms_txt.py https://ejemplo.com --output llms.txt --max-urls 200

Autor: Angel Muniz Pedraza
Licencia: MIT
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests

USER_AGENT = "llms-txt-generator/1.0 (+https://github.com/angelmunizpedraza)"
TIMEOUT = 15
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Secciones habituales y su etiqueta legible. El orden importa: define la
# prioridad con la que se presentan los bloques en el llms.txt resultante.
SECTION_LABELS: list[tuple[str, str]] = [
    (r"^/?$", "Home"),
    (r"(servicio|service|solucion|solution)", "Servicios"),
    (r"(producto|product|tienda|shop|curso|master|programa)", "Productos y formacion"),
    (r"(blog|articulo|article|noticia|news|post|guia|guide)", "Contenido y guias"),
    (r"(caso|case-stud|proyecto|portfolio|referencia)", "Casos y proyectos"),
    (r"(sobre|about|quienes|equipo|team|nosotros)", "Sobre la organizacion"),
    (r"(contacto|contact|cita|booking|reserva)", "Contacto"),
    (r"(faq|preguntas|ayuda|help|soporte|support)", "Preguntas frecuentes"),
    (r"(legal|privacidad|privacy|cookies|terminos|terms|aviso)", "Legal"),
]

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class Page:
    """Una URL del sitio con los metadatos que interesan a un LLM."""

    url: str
    title: str = ""
    description: str = ""
    section: str = "Otros"
    lastmod: str = ""

    @property
    def path(self) -> str:
        return urlparse(self.url).path or "/"


@dataclass
class SiteProfile:
    """Resultado del analisis de un sitio."""

    domain: str
    site_name: str = ""
    summary: str = ""
    pages: list[Page] = field(default_factory=list)


def clean_text(raw: str, limit: int = 160) -> str:
    """Quita etiquetas HTML, normaliza espacios y recorta a `limit` caracteres."""
    text = TAG_RE.sub(" ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    text = (
        text.replace("&amp;", "&")
        .replace("&nbsp;", " ")
        .replace("&#039;", "'")
        .replace("&quot;", '"')
    )
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "..."


def classify(path: str) -> str:
    """Asigna una seccion legible a una ruta segun patrones habituales."""
    lowered = path.lower()
    for pattern, label in SECTION_LABELS:
        if re.search(pattern, lowered):
            return label
    return "Otros"


def fetch(url: str, session: requests.Session) -> str | None:
    """Descarga una URL y devuelve su HTML, o None si falla."""
    try:
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        print(f"  aviso: no se pudo leer {url} ({exc})", file=sys.stderr)
        return None


def discover_sitemaps(base_url: str, session: requests.Session) -> list[str]:
    """Busca sitemaps en robots.txt y en las rutas convencionales."""
    found: list[str] = []

    robots = fetch(urljoin(base_url, "/robots.txt"), session)
    if robots:
        for line in robots.splitlines():
            if line.lower().startswith("sitemap:"):
                found.append(line.split(":", 1)[1].strip())

    for candidate in ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml"):
        url = urljoin(base_url, candidate)
        if url not in found:
            try:
                head = session.head(url, timeout=TIMEOUT, allow_redirects=True)
                if head.status_code == 200:
                    found.append(url)
            except requests.RequestException:
                continue

    return found


def parse_sitemap(url: str, session: requests.Session, depth: int = 0) -> list[tuple[str, str]]:
    """Devuelve [(url, lastmod)] de un sitemap, resolviendo indices anidados."""
    if depth > 2:  # cortafuegos contra indices circulares
        return []

    xml = fetch(url, session)
    if not xml:
        return []

    try:
        root = ElementTree.fromstring(xml.encode("utf-8"))
    except ElementTree.ParseError as exc:
        print(f"  aviso: sitemap ilegible en {url} ({exc})", file=sys.stderr)
        return []

    # Indice de sitemaps: recursion sobre cada hijo.
    if root.tag.endswith("sitemapindex"):
        entries: list[tuple[str, str]] = []
        for node in root.findall("sm:sitemap/sm:loc", SITEMAP_NS):
            if node.text:
                entries.extend(parse_sitemap(node.text.strip(), session, depth + 1))
        return entries

    entries = []
    for node in root.findall("sm:url", SITEMAP_NS):
        loc = node.find("sm:loc", SITEMAP_NS)
        lastmod = node.find("sm:lastmod", SITEMAP_NS)
        if loc is not None and loc.text:
            entries.append((loc.text.strip(), (lastmod.text or "").strip() if lastmod is not None else ""))
    return entries


def enrich(pages: Iterable[Page], session: requests.Session, delay: float) -> None:
    """Rellena titulo y descripcion de cada pagina leyendo su HTML."""
    for index, page in enumerate(pages, start=1):
        html = fetch(page.url, session)
        if not html:
            continue

        title_match = TITLE_RE.search(html)
        if title_match:
            page.title = clean_text(title_match.group(1), 90)

        desc_match = DESC_RE.search(html)
        if desc_match:
            page.description = clean_text(desc_match.group(1), 160)
        else:
            h1_match = H1_RE.search(html)
            if h1_match:
                page.description = clean_text(h1_match.group(1), 160)

        if index % 10 == 0:
            print(f"  {index} paginas analizadas...")
        time.sleep(delay)


def analyse(base_url: str, max_urls: int, delay: float) -> SiteProfile:
    """Recorre el sitio y construye su perfil."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    parsed = urlparse(base_url)
    profile = SiteProfile(domain=parsed.netloc)

    print(f"Buscando sitemaps en {base_url}...")
    sitemaps = discover_sitemaps(base_url, session)
    if not sitemaps:
        print("No se encontro ningun sitemap. Se usara solo la portada.", file=sys.stderr)
        entries = [(base_url, "")]
    else:
        print(f"Sitemaps encontrados: {len(sitemaps)}")
        entries = []
        for sitemap in sitemaps:
            entries.extend(parse_sitemap(sitemap, session))

    # Deduplicar preservando el orden de aparicion.
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for url, lastmod in entries:
        if url not in seen:
            seen.add(url)
            unique.append((url, lastmod))

    print(f"URLs unicas: {len(unique)} (se analizaran hasta {max_urls})")

    for url, lastmod in unique[:max_urls]:
        page = Page(url=url, lastmod=lastmod)
        page.section = classify(page.path)
        profile.pages.append(page)

    enrich(profile.pages, session, delay)

    # El titulo de la portada da nombre y resumen al sitio.
    for page in profile.pages:
        if page.path in ("/", ""):
            profile.site_name = page.title.split("|")[0].split("-")[0].strip() or profile.domain
            profile.summary = page.description
            break
    if not profile.site_name:
        profile.site_name = profile.domain

    return profile


def render(profile: SiteProfile) -> str:
    """Convierte el perfil del sitio en el contenido del fichero llms.txt."""
    lines: list[str] = [f"# {profile.site_name}", ""]

    if profile.summary:
        lines += [f"> {profile.summary}", ""]

    lines += [
        "Este fichero sigue la propuesta llms.txt para orientar a los modelos de "
        "lenguaje sobre el contenido de este sitio.",
        "",
    ]

    grouped: dict[str, list[Page]] = defaultdict(list)
    for page in profile.pages:
        grouped[page.section].append(page)

    ordered = [label for _, label in SECTION_LABELS if label in grouped]
    ordered += [key for key in grouped if key not in ordered]

    for section in ordered:
        pages = grouped[section]
        if not pages:
            continue
        lines.append(f"## {section}")
        lines.append("")
        for page in pages:
            label = page.title or page.path
            if page.description:
                lines.append(f"- [{label}]({page.url}): {page.description}")
            else:
                lines.append(f"- [{label}]({page.url})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera un fichero llms.txt a partir del sitemap de un sitio."
    )
    parser.add_argument("url", help="URL base del sitio, por ejemplo https://ejemplo.com")
    parser.add_argument("--output", "-o", default="llms.txt", help="Fichero de salida")
    parser.add_argument("--max-urls", type=int, default=100, help="Maximo de URLs a analizar")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Segundos de espera entre peticiones, para no saturar el servidor",
    )
    args = parser.parse_args()

    base_url = args.url if args.url.startswith("http") else f"https://{args.url}"

    profile = analyse(base_url, args.max_urls, args.delay)
    content = render(profile)

    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(content)

    print(f"\nListo: {args.output} ({len(profile.pages)} paginas incluidas)")
    print(f"Subelo a la raiz del dominio: {base_url.rstrip('/')}/llms.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
