import pytest

from src.pdf_handling import FPDF, generate_single_note_pdf


@pytest.mark.skipif(FPDF is None, reason="fpdf not installed")
def test_generate_single_note_pdf_handles_emoji():
    note = {"title": "Emoji 😊", "tag": "tag😊", "text": "Body with emoji 😊"}
    pdf_bytes = generate_single_note_pdf(note)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
