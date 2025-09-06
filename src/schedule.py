"""Course schedule utilities."""
from __future__ import annotations

import streamlit as st


def get_a1_schedule() -> list[dict]:
    """Return a minimal A1 schedule."""
    return [
        {
            "day": 0,
            "topic": "Tutorial",
            "chapter": "Tutorial",
            "assignment": False,
            "goal": (
                "Welcome to the A1 German course! This first chapter is a guided tour "
                "showing how the course works."
            ),
            "instruction": (
                "**Daily Focus Options**\\n"
                "- *Lesen & Hören*\\n"
                "- *Schreiben & Sprechen*\\n\\n"
                "**Tabs in the Course Interface**\\n"
                "- Overview\\n"
                "- Assignments\\n"
                "- Submit"
            ),
        },
        {
            "day": 1,
            "topic": "Lesen & Hören 0.1",
            "chapter": "0.1",
            "assignment": True,
            "goal": "You will learn to greet others in German.",
            "instruction": "Watch the video, review grammar, do the workbook, submit assignment.",
        },
    ]


def get_a2_schedule() -> list[dict]:
    """Return a minimal A2 schedule."""
    return [
        {
            "day": 0,
            "topic": "Tutorial – Course Overview",
            "chapter": "Tutorial",
            "assignment": False,
            "goal": "Orientation to how the A2 course is organized.",
            "instruction": (
                "Review how each day is structured across the four Teile.\\n\\n"
                "Practice Teil 1 before class via Custom Chat in exam mode; students who arrive unprepared often struggle. "
                "Use the Schreiben Trainer tab—Ideas Generator for brainstorming, Mark My Letter for feedback—then copy your Schreiben results together with Lesen and Hören answers and send the complete work to your tutor."
            ),
        }
    ]


def get_b1_schedule() -> list[dict]:
    """Return a minimal B1 schedule."""
    return [
        {
            "day": 0,
            "topic": "Tutorial – Course Overview",
            "chapter": "Tutorial",
            "assignment": False,
            "goal": "Orientation to how the B1 course is organized.",
            "instruction": (
                "Review how each day is structured across the four Teile."
            ),
        }
    ]


def get_b2_schedule() -> list[dict]:
    """Return a minimal B2 schedule."""
    return [
        {
            "day": 0,
            "topic": "Tutorial – Course Overview",
            "chapter": "Tutorial",
            "assignment": False,
            "goal": "Orientation to how the B2 course is organized.",
            "instruction": (
                "Review how each day is structured across the four Teile."
            ),
        }
    ]


def get_c1_schedule() -> list[dict]:
    """Return a minimal C1 schedule."""
    return [
        {
            "day": 1,
            "topic": "C1 Welcome & Orientation",
            "chapter": "0.0",
            "goal": "Get familiar with the C1 curriculum and expectations.",
            "instruction": "Read the C1 orientation, join the forum, and write a short self-intro.",
        },
        {
            "day": 2,
            "topic": "C1 Diagnostic Writing",
            "chapter": "0.1",
            "goal": "Write a sample essay for initial assessment.",
            "instruction": "Write and upload a short essay on the assigned topic.",
        },
    ]


@st.cache_data(ttl=86400)
def _load_level_schedules_cached() -> dict:
    return {
        "A1": get_a1_schedule(),
        "A2": get_a2_schedule(),
        "B1": get_b1_schedule(),
        "B2": get_b2_schedule(),
        "C1": get_c1_schedule(),
    }


def load_level_schedules() -> dict:
    if "level_schedules" not in st.session_state:
        st.session_state["level_schedules"] = _load_level_schedules_cached()
    return st.session_state["level_schedules"]


def refresh_level_schedules() -> None:
    """Clear cached level schedules so latest data is loaded on next access."""
    st.session_state.pop("level_schedules", None)
    st.cache_data.clear()


def get_level_schedules() -> dict:
    if "load_level_schedules" in globals() and callable(load_level_schedules):
        return load_level_schedules()

    def _safe(fn):
        try:
            return fn()
        except Exception:
            return []

    return {
        "A1": _safe(get_a1_schedule),
        "A2": _safe(get_a2_schedule),
        "B1": _safe(get_b1_schedule),
        "B2": _safe(get_b2_schedule),
        "C1": _safe(get_c1_schedule),
    }

