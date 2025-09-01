from src.assignment_ui import generate_receipt_pdf


def test_generate_receipt_pdf_returns_bytes():
    pdf_bytes = generate_receipt_pdf(
        "Jane Doe", "A1", "S123", "2024-01-01", 100.0, 50.0, "2024-05-01"
    )
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
