import types

import pandas as pd
import streamlit as st

from src import assignment_ui


def test_downloads_option_rendered_when_no_scores(monkeypatch):
    st.session_state.clear()
    st.session_state.update({
        "student_code": "abc",
        "student_name": "Alice",
        "student_row": {"StudentCode": "abc", "Name": "Alice", "Level": "A1"},
    })

    df = pd.DataFrame(
        {
            "student_code": ["zzz"],
            "name": ["Other"],
            "assignment": ["A1"],
            "score": ["95"],
            "date": ["2024-01-01"],
            "level": ["A1"],
        }
    )
    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda url: df)

    class DummyCtx:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "columns", lambda *a, **k: [DummyCtx(), DummyCtx(), DummyCtx()])
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "stop", lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")))
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})

    calls = []

    def fake_radio(label, options, *args, **kwargs):
        calls.append(options)
        return options[-1]

    monkeypatch.setattr(st, "radio", fake_radio)

    assignment_ui.render_results_and_resources_tab()

    assert calls[0] == ["Downloads", "Resources"]
