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


def test_refresh_button_forces_reload(monkeypatch):
    """Clicking refresh clears caches and reloads uncached scores."""

    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "abc123",
            "student_level": "A1",
            "student_name": "Alice Example",
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
            "score": ["95"],
            "date": ["2024-01-01"],
            "level": ["A1"],
            "feedback": ["Great job"],
            "answer_link": ["https://example.com"]
        }
    )

    calls = {"force_refresh": None}

    def fake_load_assignment_scores(*_args, force_refresh: bool = False, **_kwargs):
        calls["force_refresh"] = force_refresh
        return df_scores

    monkeypatch.setattr(
        assignment_ui, "load_assignment_scores", fake_load_assignment_scores
    )
    monkeypatch.setattr(
        assignment_ui, "get_assignment_summary", lambda *_a, **_k: {"missed": [], "next": None}
    )

    toasts: list[str] = []
    monkeypatch.setattr(
        assignment_ui, "refresh_with_toast", lambda message: toasts.append(message)
    )

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(
        st,
        "stop",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")),
    )
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))

    button_labels: list[str] = []

    def fake_button(label, *args, **kwargs):
        button_labels.append(label)
        return label == "🔄 Refresh scores"

    monkeypatch.setattr(st, "button", fake_button)

    tabs_calls: list[list[str]] = []

    def fake_tabs(labels, *args, **kwargs):
        tabs_calls.append(list(labels))
        return [DummyTab(label) for label in labels]

    monkeypatch.setattr(st, "tabs", fake_tabs)

    monkeypatch.setattr(st, "radio", lambda *_a, **_k: "Results PDF")

    assignment_ui.render_results_and_resources_tab()

    assert calls["force_refresh"] is True
    assert toasts == ["Refreshing scores…"]
    assert button_labels[0] == "🔄 Refresh scores"
    assert tabs_calls == [["Overview", "Missed & Next", "Feedback", "Achievements", "Downloads"]]
