"""Give every URL a human-readable section, and clean up HTML fragments."""

from __future__ import annotations

import re

# The order is the priority: it decides how the blocks are laid out in the
# generated llms.txt, so the pages a model should read first come first.
SECTION_LABELS: list[tuple[str, str]] = [
    (r"^/?$", "Home"),
    (r"(servicio|service|solucion|solution)", "Servicios"),
    (r"(producto|product|tienda|shop|curso|master|programa)", "Productos y formación"),
    (r"(blog|articulo|artículo|article|noticia|news|post|guia|guía|guide)", "Contenido y guías"),
    (r"(caso|case-stud|proyecto|portfolio|referencia)", "Casos y proyectos"),
    (r"(sobre|about|quienes|quiénes|equipo|team|nosotros)", "Sobre la organización"),
    (r"(contacto|contact|cita|booking|reserva)", "Contacto"),
    (r"(faq|preguntas|ayuda|help|soporte|support)", "Preguntas frecuentes"),
    (r"(legal|privacidad|privacy|cookies|terminos|términos|terms|aviso)", "Legal"),
]

FALLBACK_SECTION = "Otros"

TAG_RE = re.compile(r"<[^>]+>")
ENTITIES = {
    "&amp;": "&",
    "&nbsp;": " ",
    "&#039;": "'",
    "&#39;": "'",
    "&quot;": '"',
    "&lt;": "<",
    "&gt;": ">",
    "&mdash;": "—",
    "&ndash;": "–",
}


def clean_text(raw: str, limit: int = 160) -> str:
    """Strip tags, normalise whitespace and cut on a word boundary."""
    text = TAG_RE.sub(" ", raw or "")
    for entity, char in ENTITIES.items():
        text = text.replace(entity, char)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[: max(1, limit - 1)].rsplit(" ", 1)[0]
    return (cut or text[: limit - 1]) + "…"


def classify(path: str) -> str:
    """Assign a section to a path using the patterns above."""
    lowered = (path or "/").lower()
    for pattern, label in SECTION_LABELS:
        if re.search(pattern, lowered):
            return label
    return FALLBACK_SECTION


def order_sections(present: list[str]) -> list[str]:
    """Known sections first, in priority order; anything else after, as found."""
    ordered = [label for _, label in SECTION_LABELS if label in present]
    ordered += [s for s in present if s not in ordered]
    return ordered
