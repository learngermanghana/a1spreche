import types

import pandas as pd
import streamlit as st

from src import assignment_ui


class DummyTab:
    def __init__(self, label: str):
        self.label = label

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_results_tab_handles_missing_scores(monkeypatch):
    """Ensure achievements fallback renders when no graded scores are present."""

    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "abc123",
            "student_name": "Alice Example",
            "student_level": "A1",
            "student_row": {
                "StudentCode": "abc123",
                "Name": "Alice Example",
                "Level": "A1",
                "Email": "alice@example.com",
            },
        }
    )

    df_scores = pd.DataFrame(
        {
            "studentcode": ["abc123"],
            "assignment": ["Assignment 1"],
            "score": [""],
            "date": ["2024-01-01"],
            "level": ["A1"],
        }
    )

    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda *_a, **_k: df_scores)

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Transcript PDF")
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(
        st,
        "stop",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")),
    )
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})

    info_messages: list[str] = []

    def fake_info(message, *args, **kwargs):
        info_messages.append(message)
        return None

    monkeypatch.setattr(st, "info", fake_info)

    monkeypatch.setattr(
        st, "tabs", lambda labels, *a, **k: [DummyTab(label) for label in labels]
    )

    assignment_ui.render_results_and_resources_tab()

    assert "Scores will appear once assignments have been graded." in info_messages
