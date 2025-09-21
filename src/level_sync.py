"""Helpers for synchronising Streamlit level sliders with roster data."""

from __future__ import annotations

from typing import Sequence, Any


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


__all__ = ["sync_level_state"]
