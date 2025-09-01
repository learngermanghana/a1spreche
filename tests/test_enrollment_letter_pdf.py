import base64

from src.assignment_ui import generate_enrollment_letter_pdf


# small 1x1 white pixel PNG
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def test_generate_enrollment_letter_pdf_returns_bytes(monkeypatch):
    class DummyResp:
        content = PNG_BYTES

        def raise_for_status(self):
            return None

    def fake_get(url, timeout=0):
        return DummyResp()

    # Patch network call and QR code generator
    monkeypatch.setattr("src.assignment_ui.requests.get", fake_get)
    monkeypatch.setattr("src.assignment_ui.make_qr_code", lambda data: PNG_BYTES)

    pdf_bytes = generate_enrollment_letter_pdf(
        "Jane Doe", "A1", "2024-01-01", "2024-06-30"
    )
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
