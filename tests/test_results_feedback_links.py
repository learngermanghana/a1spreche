import types

import pandas as pd
import streamlit as st

from src import assignment_ui


def test_feedback_tab_shows_feedback_and_roster_links(monkeypatch):
    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "abc123",
            "student_name": "Test Student",
            "student_level": "B2",
            "student_row": {
                "StudentCode": "abc123",
                "Name": "Test Student",
                "Level": "B2",
                "Answer PDF": "https://example.com/roster-answer.pdf",
                "Feedback Notes": "See folder https://example.com/extra",
            },
        }
    )

    df_scores = pd.DataFrame(
        {
            "studentcode": ["abc123"],
            "assignment": ["Lesson 1"],
            "score": ["90"],
            "date": ["2024-02-01"],
            "level": ["B2"],
            "comment": ["Great work! Review https://example.com/rubric"],
        }
    )

    def fake_fetch_scores(*_args, **_kwargs):
        return df_scores

    monkeypatch.setattr(assignment_ui, "fetch_scores", fake_fetch_scores)
    monkeypatch.setattr(
        assignment_ui,
        "get_assignment_summary",
        lambda *a, **k: {"missed": [], "next": None},
    )

    markdown_calls: list[dict[str, object]] = []
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

    def fake_tabs(labels, *args, **kwargs):
        return [DummyTab(label) for label in labels]

    monkeypatch.setattr(st, "tabs", fake_tabs)

    def record_markdown(body, *args, **kwargs):
        markdown_calls.append({
            "body": body,
            "tab": current_tab["label"],
            "kwargs": kwargs,
        })
        return None

    monkeypatch.setattr(st, "markdown", record_markdown)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Transcript PDF")
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})
    monkeypatch.setattr(
        st,
        "stop",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called")),
    )

    assignment_ui.render_results_and_resources_tab()

    feedback_bodies = [
        call["body"]
        for call in markdown_calls
        if call["tab"] == "Feedback"
        and call["kwargs"].get("unsafe_allow_html")
        and "Great work! Review" in call["body"]
    ]
    assert feedback_bodies, "Feedback body with link should be rendered"
    assert "https://example.com/rubric" in feedback_bodies[0]
    assert "target=\"_blank\"" in feedback_bodies[0]

    resource_calls = [
        call["body"]
        for call in markdown_calls
        if call["tab"] == "Feedback"
        and call["kwargs"].get("unsafe_allow_html")
        and "https://example.com/roster-answer.pdf" in call["body"]
    ]
    assert resource_calls, "Roster reference link should be rendered"
    assert "Answer PDF" in resource_calls[0]
