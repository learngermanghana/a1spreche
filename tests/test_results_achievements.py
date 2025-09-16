import types

import pandas as pd
import streamlit as st

from src import assignment_ui


def test_results_tab_awards_gold_and_star(monkeypatch):
    """Students hitting the new thresholds should earn the matching badges."""

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
            "studentcode": ["abc123", "abc123"],
            "assignment": ["Assignment 1", "Assignment 2"],
            "score": ["86", "78"],
            "date": ["2024-01-10", "2024-01-17"],
            "level": ["A1", "A1"],
        }
    )

    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda *_a, **_k: df_scores)
    monkeypatch.setattr(
        assignment_ui,
        "get_assignment_summary",
        lambda *_a, **_k: {"missed": [], "next": None},
    )

    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})
    monkeypatch.setattr(
        st,
        "stop",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")),
    )

    current_tab = {"label": None}

    class DummyTab:
        def __init__(self, label: str):
            self.label = label

        def __enter__(self):
            current_tab["label"] = self.label
            return self

        def __exit__(self, *exc):
            current_tab["label"] = None
            return False

    monkeypatch.setattr(
        st, "tabs", lambda labels, *a, **k: [DummyTab(label) for label in labels]
    )
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Results PDF")

    achievements_output: list[str] = []

    def capture_markdown(message, *args, **kwargs):
        text = str(message)
        if current_tab["label"] == "Achievements":
            achievements_output.append(text)
        return None

    monkeypatch.setattr(st, "markdown", capture_markdown)

    assignment_ui.render_results_and_resources_tab()

    assert achievements_output, "expected achievements to render"

    gold_messages = [msg for msg in achievements_output if "Gold Badge" in msg]
    assert any("✅ 🥇 **Gold Badge**" in msg for msg in gold_messages)
    assert any("82.0%" in msg and "80% goal" in msg for msg in gold_messages)

    star_messages = [msg for msg in achievements_output if "Star Performer" in msg]
    assert any("✅ 🌟 **Star Performer**" in msg for msg in star_messages)
    assert any("86% shows your star power" in msg for msg in star_messages)

