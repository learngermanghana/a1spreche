"""Session logout utilities."""
from __future__ import annotations

import logging
from typing import Any, Callable

import streamlit as st

from falowen.sessions import destroy_session_token

from .firestore_utils import save_draft_to_db


def do_logout(
    *,
    st_module: Any = st,
    destroy_token: Callable[[str], None] = destroy_session_token,
    logger: Any = logging,
) -> None:
    """Clear session information and revoke the current session token."""
    student_code = ""

    try:
        student_code = st_module.session_state.get("student_code", "") or ""
    except Exception:
        logger.exception("Failed to capture student code on logout")

    try:
        prev_token = st_module.session_state.get("session_token", "")
        if prev_token:
            try:
                destroy_token(prev_token)
            except Exception:
                logger.exception("Token revoke failed on logout")
    except Exception:
        logger.exception("Token revoke failed on logout")

    draft_keys = {
        "coursebook_draft_key",
        "__active_draft_key",
        "falowen_chat_draft_key",
    }
    draft_prefixes = ("draft_", "falowen_chat_draft_")

    classboard_prefixes = (
        "classroom_comment_draft_",
        "q_edit_text_",
        "c_edit_text_",
    )
    try:
        for key in list(st_module.session_state.keys()):
            should_persist = key.startswith(classboard_prefixes) or key == "q_text"
            if not should_persist:
                continue

            value = st_module.session_state.get(key)
            if not value:
                continue

            try:
                save_draft_to_db(student_code, key, value)
            except Exception:
                logger.exception(
                    "Failed to persist comment draft %s for %s",
                    key,
                    student_code,
                )
    except Exception:
        logger.exception("Failed to persist classroom comment drafts on logout")

    for key in list(st_module.session_state.keys()):
        should_clear = False
        if key in draft_keys:
            should_clear = True
        elif any(key.startswith(prefix) for prefix in draft_prefixes):
            should_clear = True
        else:
            for base_key in draft_keys:
                if key.startswith(f"{base_key}__") or key.startswith(f"{base_key}_"):
                    should_clear = True
                    break

        if should_clear:
            st_module.session_state.pop(key, None)

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
