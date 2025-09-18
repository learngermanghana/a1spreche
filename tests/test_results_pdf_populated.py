import re
import re
import types
import zlib

import pandas as pd
import streamlit as st

from src import assignment_ui


class DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_results_pdf_contains_student_scores(monkeypatch):
    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "abc123",
            "student_name": "Alice Example",
            "student_level": "B1",
            "student_row": {
                "StudentCode": "abc123",
                "Name": "Alice Example",
                "Level": "B1",
                "ClassName": "Evening A",
                "Email": "alice@example.com",
            },
        }
    )

    df_scores = pd.DataFrame(
        {
            "studentcode": ["abc123"],
            "assignment": ["Assignment 1"],
            "score": ["95"],
            "date": ["2024-01-01"],
            "level": ["B1"],
        }
    )
    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda *_a, **_k: df_scores)
    monkeypatch.setattr(assignment_ui, "load_school_logo", lambda: None, raising=False)

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "columns", lambda *a, **k: [DummyCtx(), DummyCtx(), DummyCtx()])
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})
    monkeypatch.setattr(st, "stop", lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")))

    monkeypatch.setattr(st, "radio", lambda *a, **k: "Transcript PDF")

    def fake_button(label, *args, **kwargs):
        return label == "⬇️ Create & Download Transcript PDF"

    monkeypatch.setattr(st, "button", fake_button)

    captured = {}

    def fake_download_button(*args, **kwargs):
        captured["data"] = kwargs.get("data")
        captured["file_name"] = kwargs.get("file_name")
        return None

    monkeypatch.setattr(st, "download_button", fake_download_button)

    assignment_ui.render_results_and_resources_tab()

    pdf_bytes = captured.get("data")
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0

    extracted = b""
    for match in re.finditer(rb"stream\r?\n(.+?)\r?\nendstream", pdf_bytes, re.DOTALL):
        content = match.group(1)
        try:
            extracted += zlib.decompress(content)
        except zlib.error:
            extracted += content

    assert "Assignment 1".encode("utf-16-be") in extracted
    assert "95".encode("utf-16-be") in extracted
    assert "Tries".encode("utf-16-be") in extracted
    assert "Try 1".encode("utf-16-be") in extracted
    assert "Class:".encode("utf-16-be") in extracted
