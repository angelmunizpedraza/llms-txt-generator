"""Everything that touches the network, in one place, so the rest can be tested."""

from __future__ import annotations

import sys
import time

import requests

USER_AGENT = "llms-txt-generator/0.2 (+https://github.com/angelmunizpedraza/llms-txt-generator)"
TIMEOUT = 15


class Reader:
    """A polite HTTP reader: one session, a real user agent, a delay between hits."""

    def __init__(self, delay: float = 0.3, timeout: int = TIMEOUT, session=None, quiet: bool = False):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.delay = delay
        self.timeout = timeout
        self.quiet = quiet
        self.calls = 0

    def get(self, url: str) -> str | None:
        if self.calls:
            time.sleep(self.delay)
        self.calls += 1
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            if not self.quiet:
                print(f"  aviso: no se pudo leer {url} ({exc})", file=sys.stderr)
            return None

    def exists(self, url: str) -> bool:
        try:
            head = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            return head.status_code == 200
        except requests.RequestException:
            return False

    def status(self, url: str) -> int:
        """Status code of a URL, or 0 if the request itself failed."""
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            if response.status_code >= 400:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            return response.status_code
        except requests.RequestException:
            return 0
