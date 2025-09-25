import types
import pandas as pd
import streamlit as st

from src import assignment_ui

def test_enrollment_letter_blocked_with_outstanding_balance(monkeypatch):
    st.session_state.clear()
    st.session_state.update({
        "student_code": "abc",
        "student_name": "Alice",
        "student_row": {
            "StudentCode": "abc",
            "Name": "Alice",
            "Level": "A1",
            "Email": "alice@example.com",
            "Balance": "10",
        },
    })

    # No scores for this student so Downloads page is available
    df_scores = pd.DataFrame(
        {
            "student_code": ["zzz"],
            "name": ["Other"],
            "assignment": ["A1"],
            "score": ["95"],
            "date": ["2024-01-01"],
            "level": ["A1"],
        }
    )
    monkeypatch.setattr(assignment_ui, "fetch_scores", lambda url: df_scores)

    # Student has outstanding balance
    df_students = pd.DataFrame(
        [
            {
                "StudentCode": "abc",
                "ContractStart": "2024-01-01",
                "ContractEnd": "2024-06-30",
                "Balance": "10",
            }
        ]
    )
    monkeypatch.setattr(assignment_ui, "load_student_data", lambda: df_students)

    class DummyCtx:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    button_labels = []

    def fake_button(label, *args, **kwargs):
        button_labels.append(label)
        return False

    errors = []

    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    monkeypatch.setattr(st, "divider", lambda *a, **k: None)
    monkeypatch.setattr(st, "columns", lambda *a, **k: [DummyCtx(), DummyCtx(), DummyCtx()])
    monkeypatch.setattr(st, "button", fake_button)
    monkeypatch.setattr(st, "success", lambda *a, **k: None)
    monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
    monkeypatch.setattr(st, "write", lambda *a, **k: None)
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "subheader", lambda *a, **k: None)
    monkeypatch.setattr(
        st, "stop", lambda *a, **k: (_ for _ in ()).throw(AssertionError("stop called"))
    )
    monkeypatch.setattr(st, "cache_data", types.SimpleNamespace(clear=lambda: None))
    monkeypatch.setattr(st, "secrets", {})
    monkeypatch.setattr(st, "download_button", lambda *a, **k: None)

    def fake_radio(label, options, *args, **kwargs):
        if "Enrollment Letter" in options:
            return "Enrollment Letter"
        return "Downloads"

    monkeypatch.setattr(st, "radio", fake_radio)

    gen_calls = []

    def fake_generate(*a, **k):
        gen_calls.append(True)
        return b""

    monkeypatch.setattr(
        assignment_ui, "generate_enrollment_letter_pdf", fake_generate
    )

    assignment_ui.render_results_and_resources_tab()

    assert errors and errors[0] == "Outstanding balance…"
    assert "Generate Enrollment Letter" not in button_labels
    assert not gen_calls
