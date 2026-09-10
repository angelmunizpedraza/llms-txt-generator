from pathlib import Path

import pytest

from llmstxt import cli

GOOD = """# Clínica Ejemplo

> Veterinaria en Sevilla.

## Servicios

- [Cirugía de BOAS](https://example.com/boas): Qué cuesta y cuánto dura.
"""

BAD = "- [x](/relativa)\n"


def test_validate_a_good_file_exits_zero(tmp_path, capsys):
    path = tmp_path / "llms.txt"
    path.write_text(GOOD, encoding="utf-8")
    assert cli.main(["validate", str(path)]) == 0
    assert "1 links" in capsys.readouterr().out


def test_validate_a_bad_file_exits_one(tmp_path, capsys):
    path = tmp_path / "llms.txt"
    path.write_text(BAD, encoding="utf-8")
    assert cli.main(["validate", str(path)]) == 1
    assert "error" in capsys.readouterr().err


def test_strict_turns_warnings_into_a_failure(tmp_path):
    path = tmp_path / "llms.txt"
    path.write_text("# Sitio\n\n## S\n\n- [x](https://e.com/x): d\n", encoding="utf-8")
    assert cli.main(["validate", str(path)]) == 0
    assert cli.main(["validate", str(path), "--strict"]) == 1


def test_a_missing_file_exits_two(tmp_path, capsys):
    assert cli.main(["validate", str(tmp_path / "nope.txt")]) == 2
    assert "file not found" in capsys.readouterr().err


def test_generate_writes_a_file_that_validates(tmp_path, monkeypatch, reader, capsys):
    monkeypatch.setattr(cli, "Reader", lambda **kwargs: reader)
    out = tmp_path / "llms.txt"
    assert cli.main(["generate", "example.com", "-o", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Clínica Ejemplo")
    assert "## Servicios" in text
    assert "Upload it to https://example.com/llms.txt" in capsys.readouterr().out


def test_generate_accepts_a_bare_domain_and_adds_https(tmp_path, monkeypatch, reader):
    monkeypatch.setattr(cli, "Reader", lambda **kwargs: reader)
    out = tmp_path / "llms.txt"
    cli.main(["generate", "example.com", "-o", str(out)])
    assert "https://example.com/" in out.read_text(encoding="utf-8")


def test_generate_reports_when_nothing_is_found(tmp_path, monkeypatch, capsys):
    class Empty:
        def get(self, url):
            return None

        def exists(self, url):
            return False

    monkeypatch.setattr(cli, "Reader", lambda **kwargs: Empty())
    code = cli.main(["generate", "example.com", "-o", str(tmp_path / "x.txt")])
    assert code == 2
    assert "no page could be read" in capsys.readouterr().err


def test_exclude_is_passed_through(tmp_path, monkeypatch, reader):
    monkeypatch.setattr(cli, "Reader", lambda **kwargs: reader)
    out = tmp_path / "llms.txt"
    cli.main(["generate", "example.com", "-o", str(out), "--exclude", "/blog/"])
    assert "/blog/" not in out.read_text(encoding="utf-8")


def test_check_links_reports_a_dead_url(tmp_path, monkeypatch, reader, capsys):
    monkeypatch.setattr(cli, "Reader", lambda **kwargs: reader)
    path = tmp_path / "llms.txt"
    path.write_text("# S\n\n> R.\n\n## S\n\n- [muerta](https://example.com/no-existe): d\n", encoding="utf-8")
    assert cli.main(["validate", str(path), "--check-links"]) == 1
    assert "returned 404" in capsys.readouterr().err
