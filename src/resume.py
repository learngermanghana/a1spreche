"""Resume helpers for loading and displaying student progress."""
from __future__ import annotations

from typing import Optional

import streamlit as st

from . import progress_utils


def load_last_position(student_code: str) -> Optional[int]:
    """Return the last saved position for ``student_code``.

    A ``None`` result indicates no student code was supplied. Otherwise the
    value is retrieved via :func:`progress_utils.load_last_position` which
    gracefully handles missing Firestore connectivity.  Non‑positive or
    malformed values are normalised to ``None`` so callers can simply check for
    truthiness when deciding whether to render resume UI.
    """
    if not student_code:
        return None
    try:
        pos = int(progress_utils.load_last_position(student_code))
    except Exception:
        return None
    return pos if pos > 0 else None


def render_resume_banner() -> None:
    """Render a banner with an optional *Continue* button.

    The banner surfaces ``st.session_state['__last_progress']`` which callers
    populate via :func:`load_last_position`. When a valid positive position is
    present an informational banner is shown along with a primary button that
    stores the destination in ``st.session_state['section_index']`` and
    triggers a rerun so the main app can navigate to that section.
    """
    pos = st.session_state.get("__last_progress")
    
    if isinstance(pos, int) and pos > 0:
        def _jump() -> None:
            st.query_params["section"] = str(pos)
            st.rerun()

        st.info(
            f"You last stopped at section {pos} – pick up where you left off!"
        )
        st.button("Resume", on_click=_jump)


    return None


__all__ = ["load_last_position", "render_resume_banner"]
