"""llms-txt-generator — build an llms.txt from a sitemap, and check it is valid.

The llms.txt proposal is a file at the root of a domain that works as the
opposite of robots.txt: instead of blocking crawlers, it tells language models
which content matters and how it is organised.
"""

from .analyse import build_profile
from .classify import classify, clean_text
from .model import Page, SiteProfile
from .render import render
from .validate import Finding, Result, validate

__all__ = [
    "Page", "SiteProfile", "build_profile", "classify", "clean_text",
    "render", "validate", "Result", "Finding",
]
__version__ = "0.2.0"
