from src.assignment_ui import clean_for_pdf


def test_clean_for_pdf_preserves_unicode_and_strips_control_chars():
    # Include a combining character, newline, NULL byte and emoji.  The first
    # two should be normalised and the control character removed; characters
    # outside the Basic Multilingual Plane like the emoji are dropped.
    text = "a\u0308ß\nBad\x00Char😊"
    cleaned = clean_for_pdf(text)
    # Normalisation turns "a\u0308" into "ä" and newlines become spaces; the
    # NULL byte and emoji are removed entirely.
    assert cleaned == "äß BadChar"
    # Returned string should be valid UTF-8 with international characters
    cleaned.encode("utf-8")

