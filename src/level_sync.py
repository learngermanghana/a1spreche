"""Helpers for synchronising Streamlit level sliders with roster data."""

from __future__ import annotations

from typing import Sequence, Any, MutableMapping


def _coerce_level_options(level_options: Sequence[str]) -> list[str]:
    coerced: list[str] = []
    for opt in level_options:
        text = str(opt)
        if text:
            coerced.append(text)
    return coerced or [""]


def sync_level_state(
    st: Any,
    *,
    student_code: str,
    default_level: str,
    level_options: Sequence[str],
    slider_key: str,
    grammar_key: str,
    last_student_key: str = "_cchat_last_student_code",
    last_level_key: str = "_cchat_last_profile_level",
) -> str:
    """Synchronise Topic Coach and Grammar level widgets with roster updates.

    Parameters
    ----------
    st:
        Streamlit module (or compatible object) exposing ``session_state``.
    student_code:
        Currently active student identifier.
    default_level:
        Auto-detected level from the roster/profile.
    level_options:
        Permitted CEFR level options for the sliders.
    slider_key / grammar_key:
        Session-state keys for the Topic Coach and Grammar sliders.
    last_student_key / last_level_key:
        Internal bookkeeping keys used to detect when to reset state.

    Returns
    -------
    str
        The final value stored for the Topic Coach slider.
    """

    if not hasattr(st, "session_state"):
        raise AttributeError("Streamlit module must expose session_state")

    session = st.session_state
    options = _coerce_level_options(level_options)
    auto_level = str(default_level or "")
    if auto_level not in options:
        auto_level = options[0]

    student_code = student_code or ""

    previous_code = session.get(last_student_key, "")
    previous_level = session.get(last_level_key, "")
    current_slider = session.get(slider_key)
    current_grammar = session.get(grammar_key)

    roster_changed = (student_code != previous_code) or (auto_level != previous_level)

    if roster_changed or current_slider not in options:
        session[slider_key] = auto_level
    if roster_changed or current_grammar not in options:
        session[grammar_key] = auto_level

    session[last_student_key] = student_code
    session[last_level_key] = auto_level

    return session[slider_key]


def sync_assignment_level_state(
    session_state: MutableMapping[str, Any],
    *,
    student_code: str,
    detected_level: str,
    level_options: Sequence[str],
    assign_key: str,
    last_student_key: str = "_assign_last_student_code",
    last_level_key: str = "_assign_last_detected_level",
) -> str:
    """Synchronise the Assignment Helper level slider with roster updates.

    The Assignment Helper runs alongside Topic Coach but stores its level in a
    dedicated session-state key.  When a student's roster level changes (or a
    different student logs in), the slider should snap to the auto-detected
    level.  If the student keeps the same profile and adjusts the slider
    manually, their choice is preserved until the roster data changes again.
    """

    options = _coerce_level_options(level_options)
    auto_level = str(detected_level or "")
    if auto_level not in options:
        auto_level = options[0]

    student_code = student_code or ""
    previous_code = session_state.get(last_student_key, "")
    previous_level = session_state.get(last_level_key, "")
    stored_level = session_state.get(assign_key)

    roster_changed = (student_code != previous_code) or (auto_level != previous_level)

    if roster_changed or stored_level not in options:
        session_state[assign_key] = auto_level

    session_state[last_student_key] = student_code
    session_state[last_level_key] = auto_level

    return session_state[assign_key]


__all__ = ["sync_level_state", "sync_assignment_level_state"]
