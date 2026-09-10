from llmstxt.render import render
from llmstxt.validate import validate


def test_render_opens_with_the_title_and_summary(profile):
    out = render(profile)
    assert out.startswith("# Clínica Ejemplo\n")
    assert "> Veterinaria en Sevilla." in out


def test_sections_follow_the_priority_order(profile):
    out = render(profile)
    assert out.index("## Home") < out.index("## Servicios") < out.index("## Contenido y guías")


def test_a_page_without_description_is_still_linked(profile):
    out = render(profile)
    assert "- [Cómo respira un bulldog](https://example.com/blog/primer-post)\n" in out


def test_a_page_with_description_uses_the_colon_form(profile):
    assert "- [Servicios](https://example.com/servicios): Cirugía y diagnóstico." in render(profile)


def test_the_file_ends_with_exactly_one_newline(profile):
    out = render(profile)
    assert out.endswith("\n") and not out.endswith("\n\n")


def test_what_we_generate_validates_cleanly(profile):
    result = validate(render(profile), "https://example.com")
    assert result.ok, [str(f) for f in result.errors]
