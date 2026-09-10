"""The two things this tool works with: a page, and the site it belongs to."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class Page:
    """One URL of the site, with the metadata a language model can use."""

    url: str
    title: str = ""
    description: str = ""
    section: str = "Otros"
    lastmod: str = ""

    @property
    def path(self) -> str:
        return urlparse(self.url).path or "/"

    @property
    def is_home(self) -> bool:
        return self.path in ("", "/")


@dataclass
class SiteProfile:
    """The result of looking at a site."""

    domain: str
    site_name: str = ""
    summary: str = ""
    pages: list[Page] = field(default_factory=list)

    def sections(self) -> list[str]:
        seen: list[str] = []
        for page in self.pages:
            if page.section not in seen:
                seen.append(page.section)
        return seen
