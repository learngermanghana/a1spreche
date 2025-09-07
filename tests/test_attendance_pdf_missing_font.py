import zlib

from fpdf import FPDF

from src.pdf_utils import clean_for_pdf


def test_attendance_pdf_missing_font_replaces_non_latin(monkeypatch):
    pdf = FPDF()
    pdf.add_page()

    def fail_add_font(*args, **kwargs):
        raise RuntimeError("missing font")

    monkeypatch.setattr(FPDF, "add_font", fail_add_font)

    dejavu_available = True
    try:
        pdf.add_font("DejaVu", "", "font/DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "font/DejaVuSans-Bold.ttf", uni=True)
    except RuntimeError:
        dejavu_available = False
        pdf.set_font("Helvetica", size=11)

    font_family = "DejaVu" if dejavu_available else "Helvetica"
    pdf.set_font(font_family, size=12)

    txt = clean_for_pdf("Emoji 😊 und Ümlaut")
    if not dejavu_available:
        txt = txt.encode("latin1", "replace").decode("latin1")
    pdf.cell(0, 10, txt, 1, 1)

    pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
    start = pdf_bytes.find(b"stream") + 7
    end = pdf_bytes.find(b"endstream")
    content = pdf_bytes[start:end]
    try:
        data = zlib.decompress(content).decode("latin1")
    except zlib.error:
        data = content.decode("latin1")

    assert "Emoji ?" in data
    assert "Ümlaut" in data
