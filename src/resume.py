"""Resume helpers for loading and displaying student progress."""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from . import progress_utils


def load_last_position(student_code: str) -> Optional[int]:
    """Return the last saved position for ``student_code``.

    A ``None`` result indicates no student code was supplied. Otherwise the
    value is retrieved via :func:`progress_utils.load_last_position` which
    gracefully handles missing Firestore connectivity.
    """
    if not student_code:
        return None
    return progress_utils.load_last_position(student_code)


def render_resume_banner() -> None:
    """Render a simple banner if the user has previous progress.

    The banner surfaces ``st.session_state['__last_progress']`` which callers
    populate via :func:`load_last_position`.  When progress is present a small
    information message is displayed to prompt the user to continue.
    """
    pos = st.session_state.get("__last_progress")
    if isinstance(pos, int) and pos > 0:
        def _jump() -> None:
            st.query_params["section"] = str(pos)
            st.session_state["needs_rerun"] = True

        st.info(
            f"You last stopped at section {pos} – pick up where you left off!"
        )
        st.button("Resume", on_click=_jump)

    return None


__all__ = ["load_last_position", "render_resume_banner"]
