"""Resume helpers for loading and displaying student progress."""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st


def load_last_position(student_code: str) -> Optional[Any]:
    """Return the last saved position for a student.

    The real application may load this from a database. This placeholder
    implementation simply returns ``None`` to indicate no saved progress.
    """
    return None


def render_resume_banner() -> None:
    """Render a resume banner if the user has previous progress.

    The banner implementation is omitted; tests may patch this function to
    verify that it is invoked after login. This stub merely reads the cached
    progress from ``st.session_state`` for completeness.
    """
    _ = st.session_state.get("__last_progress")
    return None


__all__ = ["load_last_position", "render_resume_banner"]
