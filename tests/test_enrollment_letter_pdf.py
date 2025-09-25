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

    call_count = {"count": 0}

    def fake_get(url, timeout=0):
        call_count["count"] += 1
        return DummyResp()

    # Patch network call and QR code generator
    monkeypatch.setattr("src.assignment_ui.requests.get", fake_get)
    monkeypatch.setattr("src.assignment_ui.make_qr_code", lambda data: PNG_BYTES)

    pdf_bytes = generate_enrollment_letter_pdf(
        "Jane Doe", "A1", "2024-01-01", "2024-06-30"
    )
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    # Letterhead and watermark images should each trigger a download
    assert call_count["count"] == 2


def test_generate_enrollment_letter_pdf_handles_unicode(monkeypatch):
    class DummyResp:
        content = PNG_BYTES

        def raise_for_status(self):
            return None

    qr_calls = []

    def fake_get(url, timeout=0):
        return DummyResp()

    def fake_qr(data):
        qr_calls.append(data)
        return PNG_BYTES

    monkeypatch.setattr("src.assignment_ui.requests.get", fake_get)
    monkeypatch.setattr("src.assignment_ui.make_qr_code", fake_qr)

    name = "Jörg Müller"
    level = "B2 – Fortgeschrittene"
    pdf_bytes = generate_enrollment_letter_pdf(
        name, level, "2024-01-01", "2024-06-30"
    )
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
    assert qr_calls == [f"{name}|{level}|2024-01-01|2024-06-30"]
