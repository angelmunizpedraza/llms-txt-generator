"""Turn a SiteProfile into the text of an llms.txt file."""

from __future__ import annotations

from collections import defaultdict

from .classify import order_sections
from .model import Page, SiteProfile

INTRO = (
    "Este fichero sigue la propuesta llms.txt para orientar a los modelos de "
    "lenguaje sobre el contenido de este sitio."
)


def _line(page: Page) -> str:
    label = page.title or page.path
    if page.description:
        return f"- [{label}]({page.url}): {page.description}"
    return f"- [{label}]({page.url})"


def render(profile: SiteProfile, intro: str = INTRO) -> str:
    lines: list[str] = [f"# {profile.site_name or profile.domain}", ""]

    if profile.summary:
        lines += [f"> {profile.summary}", ""]

    if intro:
        lines += [intro, ""]

    grouped: dict[str, list[Page]] = defaultdict(list)
    for page in profile.pages:
        grouped[page.section].append(page)

    for section in order_sections(list(grouped)):
        pages = grouped[section]
        if not pages:
            continue
        lines.append(f"## {section}")
        lines.append("")
        lines.extend(_line(p) for p in pages)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
