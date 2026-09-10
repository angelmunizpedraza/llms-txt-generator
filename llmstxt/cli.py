"""llms-txt command line: generate an llms.txt, or check one you already have."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyse import build_profile
from .fetch import Reader
from .render import render
from .validate import validate

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_INPUT = 2


def _normalise(url: str) -> str:
    return url if url.startswith("http") else f"https://{url}"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="llms-txt",
        description="Generate an llms.txt from a site's sitemap, and validate the result.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="build llms.txt from a live site")
    gen.add_argument("url")
    gen.add_argument("--output", "-o", default="llms.txt")
    gen.add_argument("--max-urls", type=int, default=100)
    gen.add_argument("--delay", type=float, default=0.3)
    gen.add_argument("--include", default="", help="only URLs matching this regex")
    gen.add_argument("--exclude", default="", help="skip URLs matching this regex")
    gen.add_argument("--keep-noindex", action="store_true",
                     help="include pages marked noindex (they are dropped by default)")
    gen.add_argument("--no-validate", action="store_true",
                     help="do not check the generated file before writing it")

    val = sub.add_parser("validate", help="check an existing llms.txt")
    val.add_argument("path", help="local file, or a URL ending in /llms.txt")
    val.add_argument("--base-url", default="", help="site the file belongs to, to flag offsite links")
    val.add_argument("--check-links", action="store_true",
                     help="request every linked URL and report anything that is not 200")
    val.add_argument("--strict", action="store_true", help="treat warnings as failures too")

    return p


def _report(result, strict: bool) -> int:
    for finding in result.findings:
        stream = sys.stderr if finding.severity == "error" else sys.stdout
        print(finding, file=stream)
    print(
        f"\n{len(result.links)} links, {len(result.sections)} sections, "
        f"{len(result.errors)} errors, {len(result.warnings)} warnings"
    )
    if result.errors or (strict and result.warnings):
        return EXIT_INVALID
    return EXIT_OK


def cmd_generate(args) -> int:
    base_url = _normalise(args.url)
    reader = Reader(delay=args.delay)
    profile = build_profile(
        base_url, reader,
        max_urls=args.max_urls,
        skip_noindex=not args.keep_noindex,
        include=args.include,
        exclude=args.exclude,
    )
    if not profile.pages:
        print("llms-txt: no pages found; nothing to write", file=sys.stderr)
        return EXIT_INPUT
    if not any(p.title or p.description for p in profile.pages):
        # A file full of bare URLs tells a model nothing, and writing one
        # anyway hides the real problem: the site could not be read.
        print("llms-txt: no page could be read; check the URL and that the site is reachable",
              file=sys.stderr)
        return EXIT_INPUT

    content = render(profile)
    Path(args.output).write_text(content, encoding="utf-8")
    print(f"{args.output}: {len(profile.pages)} pages, {len(profile.sections())} sections")
    print(f"Upload it to {base_url.rstrip('/')}/llms.txt")

    if args.no_validate:
        return EXIT_OK
    result = validate(content, base_url)
    if result.findings:
        print()
        for finding in result.findings:
            print(finding)
    return EXIT_OK


def cmd_validate(args) -> int:
    source = args.path
    if source.startswith("http"):
        text = Reader(delay=0).get(source)
        if text is None:
            print(f"llms-txt: could not read {source}", file=sys.stderr)
            return EXIT_INPUT
        base = args.base_url or source
    else:
        path = Path(source)
        if not path.is_file():
            print(f"llms-txt: file not found: {source}", file=sys.stderr)
            return EXIT_INPUT
        text = path.read_text(encoding="utf-8")
        base = args.base_url

    result = validate(text, base)

    if args.check_links and result.links:
        reader = Reader(delay=0.2)
        for _, url, _ in result.links:
            code = reader.status(url)
            if code != 200:
                from .validate import Finding
                result.findings.append(Finding("error", 0, f"{url} returned {code or 'no response'}"))

    return _report(result, args.strict)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        return cmd_generate(args)
    return cmd_validate(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
