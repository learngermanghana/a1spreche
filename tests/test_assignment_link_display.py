import types
import pandas as pd
import streamlit as st

from src import assignment_ui


class DummyCol:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def metric(self, *args, **kwargs):
        pass


def setup_streamlit(monkeypatch, rr_page, outputs, df):
    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "abc",
            "student_name": "Alice",
            "student_row": {"StudentCode": "abc", "Name": "Alice", "Level": "A1"},
        }
    )

    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda url: df)
    monkeypatch.setattr(st, "markdown", lambda text, *a, **k: outputs.append(text))
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "columns", lambda spec: [DummyCol() for _ in range(len(spec) if hasattr(spec, '__len__') else spec)])
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "metric", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: rr_page)
    monkeypatch.setattr(st, "selectbox", lambda *a, **k: "A1")
    monkeypatch.setattr(st, "stop", lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")))
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})


def test_assignment_title_hyperlink(monkeypatch):
    df = pd.DataFrame(
        {
            "student_code": ["abc"],
            "name": ["Alice"],
            "assignment": ["Lesson 1"],
            "score": ["95"],
            "date": ["2024-01-01"],
            "level": ["A1"],
            "comments": [""],
            "link": ["https://example.com"],
        }
    )

    for rr_page in ["Overview", "My Scores"]:
        outputs = []
        setup_streamlit(monkeypatch, rr_page, outputs, df)
        assignment_ui.render_results_and_resources_tab()
        assert any("href=\"https://example.com\"" in o and "Lesson 1</a>" in o for o in outputs)
