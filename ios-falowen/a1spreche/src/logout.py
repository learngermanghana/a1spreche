"""Session logout utilities."""
from __future__ import annotations

import logging
from typing import Any, Callable

import streamlit as st

from falowen.sessions import destroy_session_token
from src.auth import clear_session


def do_logout(
    cookie_manager: Any,
    *,
    st_module: Any = st,
    destroy_token: Callable[[str], None] = destroy_session_token,
    clear_session_fn: Callable[[Any], None] = clear_session,
    logger: Any = logging,
) -> None:
    """Clear session information and cookies for the current user."""
    try:
        prev_token = st_module.session_state.get("session_token", "")
        if prev_token:
            try:
                destroy_token(prev_token)
            except Exception:
                logger.exception("Token revoke failed on logout")
        clear_session_fn(cookie_manager)
    except Exception:
        logger.exception("Cookie/session clear failed")
    st_module.session_state.update(
        {
            "logged_in": False,
            "student_row": {},
            "student_code": "",
            "student_name": "",
            "session_token": "",
            "student_level": "",
        }
    )
    st_module.session_state.pop("_google_btn_rendered", None)
    st_module.session_state.pop("_google_cta_rendered", None)
    st_module.session_state.pop("_ann_hash", None)
    for k in list(st_module.session_state.keys()):
        if k.startswith("__google_btn_rendered::"):
            st_module.session_state.pop(k, None)
    st_module.session_state["needs_rerun"] = True
    st_module.success("You’ve been logged out.")
