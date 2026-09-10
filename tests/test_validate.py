from llmstxt.validate import validate

GOOD = """# Clínica Ejemplo

> Veterinaria en Sevilla especializada en razas braquicéfalas.

## Servicios

- [Cirugía de BOAS](https://example.com/boas): Qué cuesta y cuánto dura la recuperación.
- [Cirugía de ojo](https://example.com/ojo): Reposición de la glándula del tercer párpado.
"""


def test_a_well_formed_file_passes():
    result = validate(GOOD, "https://example.com")
    assert result.ok
    assert result.title == "Clínica Ejemplo"
    assert result.sections == ["Servicios"]
    assert len(result.links) == 2


def test_an_empty_file_is_an_error():
    result = validate("\n\n   \n")
    assert not result.ok
    assert "empty" in result.errors[0].message


def test_a_file_without_a_title_is_an_error():
    result = validate("- [x](https://example.com/x)\n")
    assert any("no H1 title" in f.message for f in result.errors)


def test_two_titles_are_an_error():
    result = validate(GOOD + "\n# Otro título\n")
    assert any("second H1" in f.message for f in result.errors)


def test_a_file_with_no_links_is_an_error():
    result = validate("# Sitio\n\n> Resumen.\n\n## Servicios\n")
    assert any("no links" in f.message for f in result.errors)


def test_a_relative_link_is_an_error():
    result = validate("# Sitio\n\n## S\n\n- [x](/relativa)\n")
    assert any("not absolute" in f.message for f in result.errors)


def test_a_malformed_list_item_is_an_error():
    result = validate("# Sitio\n\n## S\n\n- esto no es un enlace\n")
    assert any("well-formed" in f.message for f in result.errors)


def test_a_duplicate_url_is_a_warning_not_an_error():
    text = GOOD + "- [Cirugía de BOAS otra vez](https://example.com/boas)\n"
    result = validate(text, "https://example.com")
    assert result.ok
    assert any("duplicate URL" in f.message for f in result.warnings)


def test_an_offsite_link_is_flagged_only_when_the_base_url_is_known():
    text = "# Sitio\n\n> R.\n\n## S\n\n- [Fuera](https://otro.com/x): desc\n"
    assert not any("another host" in f.message for f in validate(text).warnings)
    assert any("another host" in f.message for f in validate(text, "https://example.com").warnings)


def test_www_does_not_count_as_another_host():
    text = "# Sitio\n\n> R.\n\n## S\n\n- [Dentro](https://www.example.com/x): desc\n"
    assert not any("another host" in f.message for f in validate(text, "https://example.com").warnings)


def test_missing_summary_and_empty_section_are_warnings():
    text = "# Sitio\n\n## Vacía\n\n## Servicios\n\n- [x](https://example.com/x): desc\n"
    result = validate(text)
    messages = " ".join(f.message for f in result.warnings)
    assert "no `> summary`" in messages
    assert 'the section "Vacía" has no links' in messages
    assert result.ok


def test_too_few_descriptions_is_a_warning():
    text = "# Sitio\n\n> R.\n\n## S\n\n- [a](https://e.com/a)\n- [b](https://e.com/b)\n- [c](https://e.com/c): desc\n"
    assert any("carry a description" in f.message for f in validate(text).warnings)
