"""Session logout utilities."""
from __future__ import annotations

import logging
from typing import Any, Callable

import streamlit as st

from falowen.sessions import destroy_session_token


def do_logout(
    *,
    st_module: Any = st,
    destroy_token: Callable[[str], None] = destroy_session_token,
    logger: Any = logging,
) -> None:
    """Clear session information and revoke the current session token."""
    try:
        prev_token = st_module.session_state.get("session_token", "")
        if prev_token:
            try:
                destroy_token(prev_token)
            except Exception:
                logger.exception("Token revoke failed on logout")
    except Exception:
        logger.exception("Token revoke failed on logout")

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
    st_module.query_params.pop("t", None)
    st_module.session_state.pop("_google_btn_rendered", None)
    st_module.session_state.pop("_google_cta_rendered", None)
    st_module.session_state.pop("_ann_hash", None)
    st_module.session_state.pop("falowen_loaded_student_code", None)
    st_module.session_state.pop("falowen_conv_key", None)
    st_module.session_state.pop("falowen_loaded_key", None)
    st_module.session_state.pop("falowen_messages", None)
    for k in list(st_module.session_state.keys()):
        if k.startswith("__google_btn_rendered::"):
            st_module.session_state.pop(k, None)
    st_module.success("You’ve been logged out.")
    st_module.session_state["need_rerun"] = True
