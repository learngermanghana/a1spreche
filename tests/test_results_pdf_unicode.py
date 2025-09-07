import zlib

from fpdf import FPDF

from src.assignment_ui import clean_for_pdf


def test_pdf_cells_preserve_unicode():
    pdf = FPDF()
    pdf.add_font("DejaVu", "", "font/DejaVuSans.ttf", uni=True)
    pdf.add_page()
    pdf.set_font("DejaVu", "", 12)
    # Text with umlauts and ß
    table_txt = clean_for_pdf("Grüße")
    field_txt = clean_for_pdf("Straße")
    pdf.cell(0, 10, table_txt, 1, 1)
    pdf.multi_cell(0, 10, field_txt)
    pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
    start = pdf_bytes.find(b"stream") + 7
    end = pdf_bytes.find(b"endstream")
    content = pdf_bytes[start:end]
    try:
        data = zlib.decompress(content)
    except zlib.error:
        data = content
    assert b"\x00G\x00r\x00\xfc\x00\xdf\x00e" in data
    assert b"\x00S\x00t\x00r\x00a\x00\xdf\x00e" in data
