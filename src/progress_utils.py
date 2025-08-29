"""Progress helpers for tracking user's last position.

This module stores and retrieves the last position a student reached in the
application.  It relies on Firestore for persistence but safely handles
missing dependencies or connectivity issues.  On failure, it logs the error
and surfaces a Streamlit warning instead of raising an exception.
"""

from __future__ import annotations

import logging
import streamlit as st

try:  # Firestore is optional in certain environments
    from firebase_admin import firestore  # type: ignore
    from falowen.sessions import db  # pragma: no cover - side effect import
except Exception:  # pragma: no cover - Firestore may be unavailable
    db = None  # type: ignore


def _progress_doc_ref(student_code: str):
    """Return the Firestore document reference for the student's progress."""
    if db is None:
        return None
    return db.collection("falowen_progress").document(student_code)


def save_last_position(student_code: str, position: int) -> None:
    """Persist ``position`` as the student's last seen position."""
    ref = _progress_doc_ref(student_code)
    if ref is None:
        return
    try:
        ref.set({"last_position": int(position)}, merge=True)
    except Exception as exc:  # pragma: no cover - depends on Firestore
        logging.exception("Failed to save last position for %s", student_code)
        st.warning(f"Could not save position: {exc}")


def load_last_position(student_code: str) -> int:
    """Load the last stored position for ``student_code``.

    If no progress exists yet, the position is initialised to ``0`` and saved
    to Firestore for next time.
    """
    ref = _progress_doc_ref(student_code)
    if ref is None:
        return 0
    try:
        snap = ref.get()
        if not snap.exists:
            save_last_position(student_code, 0)
            return 0
        data = snap.to_dict() or {}
        return int(data.get("last_position", 0))
    except Exception as exc:  # pragma: no cover - depends on Firestore
        logging.exception("Failed to load last position for %s", student_code)
        st.warning(f"Could not load position: {exc}")
        return 0


__all__ = [
    "load_last_position",
    "save_last_position",
]
