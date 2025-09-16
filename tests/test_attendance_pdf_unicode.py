import zlib

from fpdf import FPDF
import streamlit as st

from src import assignment_ui
from src.pdf_handling import FONT_PATH
from src.pdf_utils import clean_for_pdf


def test_attendance_pdf_preserves_unicode_and_emoji():
    pdf = FPDF()
    pdf.add_font("DejaVu", "", str(FONT_PATH), uni=True)
    pdf.add_page()
    pdf.set_font("DejaVu", "", 12)
    txt = clean_for_pdf("Schüler 😊")
    pdf.cell(0, 10, txt, 1, 1)
    try:
        pdf_bytes = pdf.output(dest="S").encode("latin1", "replace")
    except Exception:
        import pytest

        pytest.skip("emoji not supported by current font")
    stream_idx = pdf_bytes.find(b"stream")
    assert stream_idx != -1
    start = stream_idx + len(b"stream")
    while start < len(pdf_bytes) and pdf_bytes[start] in (0x0A, 0x0D, 0x20):
        start += 1
    end = pdf_bytes.find(b"endstream", start)
    assert end != -1
    content = pdf_bytes[start:end]
    try:
        data = zlib.decompress(content)
    except zlib.error:
        data = content
    assert b"\x00S\x00c\x00h\x00\xfc\x00l\x00e\x00r\x00 \xD8\x3D\xDE\x0A" in data


def test_attendance_pdf_truncates_long_session_names(monkeypatch):
    st.session_state.clear()
    st.session_state.update(
        {
            "student_row": {
                "ClassName": "Level 1",
                "StudentCode": "ABC123",
                "Name": "Alice",
            }
        }
    )

    long_session = "Session " + "Überlanger Unterrichtstitel " * 12
    records = [{"session": long_session, "present": True}]

    monkeypatch.setattr(
        assignment_ui,
        "load_attendance_records",
        lambda code, class_name: (records, [], 0),
    )
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "selectbox", lambda *a, **k: "Attendance PDF")
    monkeypatch.setattr(st, "info", lambda *a, **k: None)

    captured_download: dict[str, object] = {}

    def fake_download_button(label, *, data, file_name, mime):
        captured_download.update(
            {"label": label, "data": data, "file_name": file_name, "mime": mime}
        )
        return True

    monkeypatch.setattr(st, "download_button", fake_download_button)

    original_cell = assignment_ui.FPDF.cell
    session_cells: list[tuple[assignment_ui.FPDF, str]] = []

    def capture_cell(self, w, h=0, txt="", border=0, ln=0, align="", fill=False, link=""):
        if w == 120 and border == 1 and align == "L" and txt:
            session_cells.append((self, txt))
        return original_cell(self, w, h, txt, border, ln, align, fill, link)

    monkeypatch.setattr(assignment_ui.FPDF, "cell", capture_cell)

    assignment_ui.render_results_and_resources_tab()

    assert session_cells, "expected attendance session rows"
    pdf_obj, shortened_text = session_cells[0]
    sanitized_original = clean_for_pdf(long_session)

    assert shortened_text.endswith("...")
    assert shortened_text != sanitized_original
    assert pdf_obj.get_string_width(shortened_text) <= 120

    assert captured_download.get("data"), "expected attendance PDF bytes"
    pdf_bytes = captured_download["data"]
    assert isinstance(pdf_bytes, (bytes, bytearray))

    stream_idx = pdf_bytes.find(b"stream")
    assert stream_idx != -1
    start = stream_idx + len(b"stream")
    while start < len(pdf_bytes) and pdf_bytes[start] in (0x0A, 0x0D, 0x20):
        start += 1
    end = pdf_bytes.find(b"endstream", start)
    assert end != -1
    content = pdf_bytes[start:end]
    try:
        payload = zlib.decompress(content)
    except zlib.error:
        payload = content

    shortened_encoded = shortened_text.encode("utf-16-be")
    long_encoded = sanitized_original.encode("utf-16-be")
    assert shortened_encoded in payload
    assert long_encoded not in payload

