# llms-txt-generator

**Build an `llms.txt` from a site's sitemap — and check the one you already published is not broken.**

[![CI](https://github.com/angelmunizpedraza/llms-txt-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/angelmunizpedraza/llms-txt-generator/actions)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What `llms.txt` is

A file at the root of a domain that works as the opposite of `robots.txt`: instead of blocking crawlers, it tells language models which content matters and how it is organised. A good one is a short, sectioned, linked map of the site with a one-line description per page — because the description is what a model quotes.

## Two commands

```bash
llms-txt generate example.com --output llms.txt
llms-txt validate llms.txt --base-url https://example.com --check-links
```

`generate` reads `robots.txt`, follows every sitemap it declares (plus the conventional paths), walks sitemap indexes, drops duplicates, fetches each page for its title and description, groups the URLs into readable sections, and writes the file. `validate` is the half most tools skip.

## Why the validator exists

Generating the file is easy. What costs traffic is publishing one that is quietly malformed, so here is what `validate` refuses:

| Severity | Check |
|---|---|
| error | The file is empty, or has no `# Title`, or has two |
| error | No links at all — the file tells a model nothing |
| error | A list item that is not a well-formed `- [label](url)` |
| error | A relative link: a model resolving `/servicios` has nothing to resolve it against |
| warning | A duplicate URL, an empty section, a link to another host, a link with no label |
| warning | No `> summary` line under the title |
| warning | Fewer than half the links carry a description |
| optional | `--check-links` requests every URL and fails on anything that is not 200 |

`--strict` turns warnings into a failure too, so the whole thing can gate a deploy: exit `0` valid, `1` invalid, `2` bad input.

## What `generate` does that a sitemap dump does not

- **Sections instead of a flat list.** URLs are grouped into Home, Servicios, Productos y formación, Contenido y guías, Casos y proyectos, Sobre la organización, Contacto, Preguntas frecuentes and Legal, matched on both Spanish and English path patterns, and emitted in that priority order. A model reads top-down; the cookie policy should not be the first thing it sees.
- **`noindex` pages are dropped** by default (`--keep-noindex` if you disagree). A page you told Google to ignore has no business being recommended to a model.
- **The description falls back to the H1** when there is no meta description, rather than emitting a bare URL.
- **The site name comes from the home title**, cut at the first separator, so you get `Clínica Ejemplo` and not `Clínica Ejemplo | Veterinaria en Sevilla | Inicio`.
- **`--include` / `--exclude`** take regexes, for the usual "everything except `/tag/` and `/author/`".
- **Politeness is not optional**: one session, a real user agent, and `--delay` between requests.

## Install

```bash
pip install -e .
```

## Output

```
# Clínica Ejemplo

> Clínica veterinaria en Sevilla especializada en razas braquicéfalas.

Este fichero sigue la propuesta llms.txt para orientar a los modelos de
lenguaje sobre el contenido de este sitio.

## Servicios

- [Servicios](https://example.com/servicios): Cirugía, diagnóstico y urgencias.

## Contenido y guías

- [Cómo respira un bulldog](https://example.com/blog/primer-post): Qué es el síndrome braquicéfalo y cuándo operar.
```

`examples/llms.txt` is that file in full; `llms-txt validate examples/llms.txt` returns clean, and CI checks that it still does.

## In CI

```yaml
- name: llms.txt must stay valid
  run: llms-txt validate public/llms.txt --base-url https://example.com --strict
```

## Project layout

```
llmstxt/
  model.py      Page and SiteProfile
  classify.py   path → section, and HTML fragment → clean text
  sitemap.py    robots.txt, sitemap indexes, dedupe (no network: a reader is injected)
  analyse.py    base URL → SiteProfile
  render.py     SiteProfile → llms.txt
  validate.py   llms.txt → findings
  fetch.py      the only module that touches the network
  cli.py        llms-txt generate / llms-txt validate
tests/          52 tests, no network required
```

The network lives in exactly one module and is injected everywhere else, which is why the whole suite runs offline in under a second.

## Related tools

Part of a set of nine open-source tools I use on client work — all Python, MIT, deterministic, no API keys:

[geo-check](https://github.com/angelmunizpedraza/geo-check) · [render-gap](https://github.com/angelmunizpedraza/render-gap) · [citeable](https://github.com/angelmunizpedraza/citeable) · [serp-to-ai-diff](https://github.com/angelmunizpedraza/serp-to-ai-diff) · [ai-visibility-tracker](https://github.com/angelmunizpedraza/ai-visibility-tracker) · [linkjuice](https://github.com/angelmunizpedraza/linkjuice) · [seo-audit](https://github.com/angelmunizpedraza/seo-audit) · [ga4-report](https://github.com/angelmunizpedraza/ga4-report)

`geo-check` asks whether the AI crawlers are allowed in. `render-gap` asks whether anything was there when they arrived. `citeable` asks whether it was worth quoting.

## Licence

MIT — Ángel Muñiz Pedraza · [LinkedIn](https://www.linkedin.com/in/angel-muniz-seo) · angelhd029@gmail.com
