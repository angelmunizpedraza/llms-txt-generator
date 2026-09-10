from llmstxt.classify import classify, clean_text, order_sections


def test_home_is_matched_by_the_empty_path():
    assert classify("/") == "Home"
    assert classify("") == "Home"


def test_sections_are_matched_in_priority_order():
    # /servicios/blog contains both patterns; "Servicios" is declared first.
    assert classify("/servicios/blog") == "Servicios"


def test_spanish_and_english_paths_land_in_the_same_section():
    assert classify("/about-us") == classify("/sobre-nosotros")
    assert classify("/privacy-policy") == classify("/politica-de-privacidad") == "Legal"


def test_unknown_paths_fall_back():
    assert classify("/xyz-123") == "Otros"


def test_clean_text_strips_tags_entities_and_whitespace():
    assert clean_text("<p>Hola   &amp;  <b>adiós</b></p>") == "Hola & adiós"


def test_clean_text_cuts_on_a_word_boundary():
    out = clean_text("uno dos tres cuatro cinco seis siete", limit=20)
    assert out.endswith("…")
    assert len(out) <= 20
    assert not out.rstrip("…").endswith(" ")


def test_clean_text_leaves_short_text_alone():
    assert clean_text("corto", limit=50) == "corto"


def test_order_sections_puts_known_ones_first_and_keeps_the_rest():
    out = order_sections(["Otros", "Legal", "Home", "Inventada"])
    assert out[0] == "Home"
    assert out.index("Legal") < out.index("Otros")
    assert "Inventada" in out
