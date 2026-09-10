#!/usr/bin/env python3
"""Deprecated entry point, kept so old links and bookmarks keep working.

Version 0.2 split this script into the `llmstxt` package and added a
validator. Use `llms-txt generate ...` (or `python -m llmstxt.cli`) instead.
"""

import sys

from llmstxt.cli import main

if __name__ == "__main__":
    print(
        "generate_llms_txt.py is deprecated: use `llms-txt generate <url>`.\n"
        "Running it for you now.\n",
        file=sys.stderr,
    )
    raise SystemExit(main(["generate"] + sys.argv[1:]))
