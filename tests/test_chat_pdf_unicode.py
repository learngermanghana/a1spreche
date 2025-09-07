import pytest

from src.pdf_handling import FPDF, generate_chat_pdf


@pytest.mark.skipif(FPDF is None, reason="fpdf not installed")
def test_generate_chat_pdf_handles_unicode_and_emoji():
    messages = [
        {"role": "assistant", "content": "Hello 😊"},
        {"role": "user", "content": "Numbers: ①②③"},
    ]
    pdf_bytes = generate_chat_pdf(messages)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
