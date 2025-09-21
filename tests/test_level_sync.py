from types import SimpleNamespace

import pytest

from src.level_sync import sync_level_state


@pytest.fixture
def level_options():
    return ["A1", "A2", "B1", "B2"]


def test_sync_level_state_resets_on_profile_change(level_options):
    st = SimpleNamespace(session_state={})

    # Initial roster load seeds both sliders
    sync_level_state(
        st,
        student_code="stu1",
        default_level="A2",
        level_options=level_options,
        slider_key="slider",
        grammar_key="grammar",
    )
    assert st.session_state["slider"] == "A2"
    assert st.session_state["grammar"] == "A2"

    # Learner customises their sliders during the session
    st.session_state["slider"] = "B2"
    st.session_state["grammar"] = "B2"

    # When the roster updates to a new level for the same student,
    # both widgets should snap back to the fresh profile value.
    sync_level_state(
        st,
        student_code="stu1",
        default_level="B1",
        level_options=level_options,
        slider_key="slider",
        grammar_key="grammar",
    )
    assert st.session_state["slider"] == "B1"
    assert st.session_state["grammar"] == "B1"

    system_prompt = f"CEFR level: {st.session_state['slider']}."
    assert system_prompt.endswith("B1.")


def test_sync_level_state_preserves_manual_choice(level_options):
    st = SimpleNamespace(session_state={})

    sync_level_state(
        st,
        student_code="stu1",
        default_level="A2",
        level_options=level_options,
        slider_key="slider",
        grammar_key="grammar",
    )

    # User adjusts level but roster remains unchanged.
    st.session_state["slider"] = "B2"
    st.session_state["grammar"] = "B2"

    sync_level_state(
        st,
        student_code="stu1",
        default_level="A2",
        level_options=level_options,
        slider_key="slider",
        grammar_key="grammar",
    )

    assert st.session_state["slider"] == "B2"
    assert st.session_state["grammar"] == "B2"
