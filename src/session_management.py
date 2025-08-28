"""Session management utilities for a1sprechen."""

from __future__ import annotations

import logging
from typing import Any, Protocol

import pandas as pd
import streamlit as st

from src.stats import get_student_level


class CookieLike(Protocol):
    def ready(self) -> bool: ...


def bootstrap_cookie_manager(cm: CookieLike) -> CookieLike:
    """Return the cookie manager instance and gate on readiness if available."""
    ready_fn = getattr(cm, "ready", None)
    if callable(ready_fn) and not bool(ready_fn()):
        st.stop()
    return cm


def bootstrap_state() -> None:
    """Initialise default values in ``st.session_state``."""
    defaults = {
        "logged_in": False,
        "student_row": {},
        "student_code": "",
        "student_name": "",
        "student_level": "",
        "session_token": "",
        "cookie_synced": False,
        "__last_refresh": 0.0,
        "__ua_hash": "",
        "_oauth_state": "",
        "_oauth_code_redeemed": "",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def determine_level(sc: str, row: Any) -> str:
    """Resolve a student's level from a row or fallback helper."""
    level = ""
    if isinstance(row, (dict, pd.Series)):
        level = row.get("Level", "")
    if not level and sc:
        try:
            level = get_student_level(sc) or ""
        except Exception as exc:  # pragma: no cover - defensive
            logging.exception("Failed to look up student level")
            level = ""
    return str(level or "").strip()


def ensure_student_level() -> str:
    """Ensure ``st.session_state['student_level']`` is populated."""
    if st.session_state.get("student_level"):
        return st.session_state["student_level"]
    sc = st.session_state.get("student_code", "")
    row = st.session_state.get("student_row", {})
    level = determine_level(sc, row)
    st.session_state["student_level"] = level
    return level


__all__ = [
    "bootstrap_cookie_manager",
    "bootstrap_state",
    "determine_level",
    "ensure_student_level",
    "CookieLike",
]
