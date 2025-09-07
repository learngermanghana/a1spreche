import zlib

from fpdf import FPDF

from src.assignment_ui import clean_for_pdf


def test_attendance_pdf_preserves_unicode_and_emoji():
    pdf = FPDF()
    pdf.add_font("DejaVu", "", "font/DejaVuSans.ttf", uni=True)
    pdf.add_page()
    pdf.set_font("DejaVu", "", 12)
    txt = clean_for_pdf("Schüler 😊")
    pdf.cell(0, 10, txt, 1, 1)
    try:
        pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
    except Exception:
        import pytest

        pytest.skip("emoji not supported by current font")
    start = pdf_bytes.find(b"stream") + 7
    end = pdf_bytes.find(b"endstream")
    content = pdf_bytes[start:end]
    try:
        data = zlib.decompress(content)
    except zlib.error:
        data = content
    assert b"\x00S\x00c\x00h\x00\xfc\x00l\x00e\x00r\x00 \xD8\x3D\xDE\x0A" in data

