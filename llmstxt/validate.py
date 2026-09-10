"""Check an existing llms.txt against the shape the proposal describes.

Generating the file is the easy half. The half that actually costs people
traffic is publishing one that is malformed, points at redirects, or lists the
cookie policy above the services — so this module is the reason the tool is
called a generator *and* a validator.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

H1_RE = re.compile(r"^#\s+(.+?)\s*$")
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
QUOTE_RE = re.compile(r"^>\s*(.+?)\s*$")
LINK_RE = re.compile(r"^-\s+\[(?P<label>[^\]]*)\]\((?P<url>[^)\s]+)\)(?::\s*(?P<desc>.+))?\s*$")

MAX_BYTES = 200_000
MIN_DESCRIBED_RATIO = 0.5

SEVERITIES = ("error", "warning", "notice")


@dataclass
class Finding:
    severity: str
    line: int
    message: str

    def __str__(self) -> str:  # pragma: no cover - convenience only
        where = f"line {self.line}" if self.line else "file"
        return f"{self.severity}: {where}: {self.message}"


@dataclass
class Result:
    findings: list[Finding]
    title: str = ""
    summary: str = ""
    sections: list[str] = None  # type: ignore[assignment]
    links: list[tuple[str, str, str]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.sections is None:
            self.sections = []
        if self.links is None:
            self.links = []

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(text: str, base_url: str = "") -> Result:
    """Validate the content of an llms.txt file.

    `base_url` is optional; when given, links pointing at another host are
    reported, because an llms.txt that sends a model somewhere else is almost
    always a copy-paste accident.
    """
    findings: list[Finding] = []
    result = Result(findings=findings)

    if len(text.encode("utf-8")) > MAX_BYTES:
        findings.append(Finding("warning", 0, f"the file is over {MAX_BYTES // 1000} KB; consider trimming it"))

    lines = text.splitlines()
    if not any(line.strip() for line in lines):
        findings.append(Finding("error", 0, "the file is empty"))
        return result

    seen_urls: dict[str, int] = {}
    current_section = ""
    section_has_link: dict[str, bool] = {}
    described = 0
    host = urlparse(base_url).netloc.lower().removeprefix("www.") if base_url else ""

    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip()
        if not line.strip():
            continue

        h1 = H1_RE.match(line)
        if h1:
            if result.title:
                findings.append(Finding("error", number, "a second H1: the file must have exactly one title"))
            else:
                result.title = h1.group(1)
            continue

        h2 = H2_RE.match(line)
        if h2:
            current_section = h2.group(1)
            if current_section in result.sections:
                findings.append(Finding("warning", number, f'the section "{current_section}" appears twice'))
            else:
                result.sections.append(current_section)
            section_has_link.setdefault(current_section, False)
            continue

        quote = QUOTE_RE.match(line)
        if quote:
            if not result.summary:
                result.summary = quote.group(1)
            continue

        if line.lstrip().startswith("-"):
            match = LINK_RE.match(line.strip())
            if not match:
                findings.append(Finding("error", number, "list item is not a well-formed `- [label](url)` link"))
                continue
            url = match.group("url")
            label = match.group("label").strip()
            desc = (match.group("desc") or "").strip()
            result.links.append((label, url, desc))
            if current_section:
                section_has_link[current_section] = True

            if not label:
                findings.append(Finding("warning", number, "link has no label"))
            if not urlparse(url).scheme:
                findings.append(Finding("error", number, f"link is not absolute: {url}"))
            elif host:
                link_host = urlparse(url).netloc.lower().removeprefix("www.")
                if link_host and link_host != host:
                    findings.append(Finding("warning", number, f"link points to another host: {link_host}"))
            if url in seen_urls:
                findings.append(Finding("warning", number, f"duplicate URL, first seen on line {seen_urls[url]}"))
            else:
                seen_urls[url] = number
            if desc:
                described += 1
            continue

        if not current_section and not result.title:
            findings.append(Finding("notice", number, "text before the H1 title"))

    if not result.title:
        findings.append(Finding("error", 0, "no H1 title: an llms.txt must start with `# Site name`"))
    if not result.summary:
        findings.append(Finding("warning", 0, "no `> summary` line under the title"))
    if not result.links:
        findings.append(Finding("error", 0, "no links at all: the file tells a model nothing"))
    if not result.sections:
        findings.append(Finding("warning", 0, "no `## Section` headings: everything is in one undifferentiated list"))

    for section, has_link in section_has_link.items():
        if not has_link:
            findings.append(Finding("warning", 0, f'the section "{section}" has no links'))

    if result.links:
        ratio = described / len(result.links)
        if ratio < MIN_DESCRIBED_RATIO:
            findings.append(Finding(
                "warning", 0,
                f"only {round(100 * ratio)}% of the links carry a description; a model quotes the description",
            ))

    return result
