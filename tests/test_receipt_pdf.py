from src.assignment_ui import generate_receipt_pdf


def test_generate_receipt_pdf_returns_bytes():
    pdf_bytes = generate_receipt_pdf(
        "Jane Doe", "A1", "S123", "2024-01-01", 100.0, 50.0, "2024-05-01"
    )
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    import re, zlib

    extracted = b""
    for match in re.finditer(rb"stream\r?\n(.+?)\r?\nendstream", pdf_bytes, re.DOTALL):
        data = match.group(1)
        try:
            extracted += zlib.decompress(data)
        except Exception:
            extracted += data
    assert b"\x00c\x00e\x00d\x00i\x00s" in extracted
    assert b"\xe2\x82\xb5" not in extracted
