from src.assignment_ui import clean_for_pdf


def test_clean_for_pdf_handles_non_latin1():
    text = "Score ✓ and emoji 😊"
    cleaned = clean_for_pdf(text)
    # Should encode to Latin-1 without raising an exception
    cleaned.encode("latin-1")
    # Non-Latin-1 characters should be replaced
    assert cleaned == "Score ? and emoji ?"

