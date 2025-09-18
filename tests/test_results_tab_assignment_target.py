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
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Transcript PDF")
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


def test_results_tab_collapses_duplicate_attempts(monkeypatch):
    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "dup-learner",
            "student_name": "Retry Student",
            "student_level": "B2",
            "student_row": {
                "StudentCode": "dup-learner",
                "Name": "Retry Student",
                "Level": "B2",
                "Email": "retry@example.com",
            },
        }
    )

    df_scores = pd.DataFrame(
        {
            "studentcode": ["dup-learner", "dup-learner"],
            "assignment": ["Speaking Practice", "Speaking Practice"],
            "score": ["70", "88"],
            "date": ["2024-02-01", "2024-02-05"],
            "level": ["B2", "B2"],
        }
    )

    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda *_a, **_k: df_scores)

    written_dfs: list[pd.DataFrame] = []
    write_messages: list[str] = []
    markdown_messages: list[str] = []

    def fake_write(*args, **_kwargs):
        for arg in args:
            if isinstance(arg, pd.DataFrame):
                written_dfs.append(arg)
            elif isinstance(arg, str):
                write_messages.append(arg)
        return None

    def fake_markdown(message, *args, **_kwargs):
        if isinstance(message, str):
            markdown_messages.append(message)
        return None

    monkeypatch.setattr(st, "markdown", fake_markdown)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", fake_write)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Transcript PDF")
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

    assert written_dfs, "overview table was not rendered"
    overview_df = None
    for candidate in written_dfs:
        lowered = [str(col).lower() for col in candidate.columns]
        if "tries" in lowered:
            overview_df = candidate
            break
    assert overview_df is not None, "No overview DataFrame with tries column found"
    tries_col_idx = [str(col).lower() for col in overview_df.columns].index("tries")
    tries_value = overview_df.iloc[0, tries_col_idx]
    assert tries_value == 2, f"Expected 2 tries, got {tries_value!r}"

    combined_messages = " ".join(write_messages + markdown_messages)
    assert "Try 2" in combined_messages
    assert any("Average score: 88.0%" in msg for msg in write_messages)
