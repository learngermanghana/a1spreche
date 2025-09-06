import types

import pandas as pd
import pytest
import streamlit as st

from src import assignment_ui


class DummyCtx:
    def __init__(self, metrics):
        self.metrics = metrics

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def metric(self, label, value, *a, **k):
        self.metrics[label] = value


@pytest.mark.parametrize("level, expected", [("A1", 17), ("A2", 28)])
def test_overview_shows_updated_totals(monkeypatch, level, expected):
    st.session_state.clear()
    st.session_state.update(
        {
            "student_code": "abc",
            "student_name": "Alice",
            "student_row": {"StudentCode": "abc", "Name": "Alice", "Level": level},
        }
    )

    df = pd.DataFrame(
        {
            "student_code": ["abc"],
            "name": ["Alice"],
            "assignment": ["1"],
            "score": ["90"],
            "date": ["2024-01-01"],
            "level": [level],
        }
    )
    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda url: df)

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    metrics = {}

    def fake_columns(spec):
        count = spec if isinstance(spec, int) else len(spec)
        return [DummyCtx(metrics) for _ in range(count)]

    monkeypatch.setattr(st, "columns", fake_columns)
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda *a, **k: None)
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(st, "caption", lambda *a, **k: None)
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})
    monkeypatch.setattr(st, "selectbox", lambda *a, **k: level)
    monkeypatch.setattr(st, "radio", lambda *a, **k: "Overview")
    monkeypatch.setattr(
        st, "stop", lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called"))
    )

    assignment_ui.render_results_and_resources_tab()
    assert metrics["Total Assignments"] == expected
