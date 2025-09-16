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


def test_results_tab_uses_level_target(monkeypatch):
    """Ensure overview and achievements reflect the level assignment target."""

    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "a1-learner",
            "student_name": "Test Student",
            "student_level": "A1",
            "student_row": {
                "StudentCode": "a1-learner",
                "Name": "Test Student",
                "Level": "A1",
                "Email": "test@example.com",
            },
        }
    )

    df_scores = pd.DataFrame(
        {
            "studentcode": ["a1-learner"] * 5,
            "assignment": [
                "Lesen & Hören 0.1",
                "Lesen & Hören 0.2",
                "Lesen & Hören 1.1",
                "Lesen & Hören 1.2",
                "Lesen & Hören 2",
            ],
            "score": ["95", "88", "90", "100", "85"],
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
            "level": ["A1"] * 5,
        }
    )

    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda *_a, **_k: df_scores)

    writes: list[str] = []
    markdowns: list[str] = []

    def fake_write(*args, **_kwargs):
        for arg in args:
            if isinstance(arg, str):
                writes.append(arg)
        return None

    def fake_markdown(message, *args, **_kwargs):
        if isinstance(message, str):
            markdowns.append(message)
        return None

    monkeypatch.setattr(st, "markdown", fake_markdown)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", fake_write)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Results PDF")
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})
    monkeypatch.setattr(
        st,
        "stop",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")),
    )
    monkeypatch.setattr(
        st, "tabs", lambda labels, *a, **k: [DummyTab(label) for label in labels]
    )

    assignment_ui.render_results_and_resources_tab()

    assert "Completed assignments: 5 / 19" in writes

    trophy_lines = [msg for msg in markdowns if "Completion Trophy" in msg]
    assert trophy_lines, "Completion trophy status was not rendered"
    assert trophy_lines[0].startswith("🔒"), "Trophy should remain locked at 5/19"
    assert "5/19" in trophy_lines[0]
