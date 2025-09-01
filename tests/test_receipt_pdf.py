from src.assignment_ui import generate_receipt_pdf


def _extract_text(pdf_bytes: bytes) -> str:
    import re, zlib

    extracted = b""
    for match in re.finditer(rb"stream\r?\n(.+?)\r?\nendstream", pdf_bytes, re.DOTALL):
        data = match.group(1)
        try:
            data = zlib.decompress(data)
        except Exception:
            pass
        extracted += data
    return extracted.replace(b"\x00", b"").decode("latin1", errors="ignore")


def test_generate_receipt_pdf_returns_bytes():
    pdf_bytes = generate_receipt_pdf(
        "Jane Doe", "A1", "S123", "2024-01-01", 100.0, 50.0, "2024-05-01"
    )
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    text = _extract_text(pdf_bytes)
    assert "cedis" in text
    assert "₵" not in text  # no cedi symbol


def test_generate_receipt_pdf_full_payment_shows_status():
    pdf_bytes = generate_receipt_pdf(
        "Jane Doe", "A1", "S123", "2024-01-01", 100.0, 0.0, "2024-05-01"
    )
    text = _extract_text(pdf_bytes)
    assert "Status: Full payment" in text


def test_generate_receipt_pdf_installment_shows_balance():
    pdf_bytes = generate_receipt_pdf(
        "Jane Doe", "A1", "S123", "2024-01-01", 75.0, 25.0, "2024-05-01"
    )
    text = _extract_text(pdf_bytes)
    from src.utils.currency import format_cedis

    assert "Installment" in text
    assert format_cedis(25.0) in text
