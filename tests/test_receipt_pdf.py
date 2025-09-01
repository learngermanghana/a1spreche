from src.assignment_ui import generate_receipt_pdf


def test_generate_receipt_pdf_returns_bytes():
    pdf_bytes = generate_receipt_pdf("Jane Doe", "A1", 100.0, 50.0, "2024-05-01")
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
