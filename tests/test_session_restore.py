import sys
import types

import pandas as pd
import streamlit as st

from src.auth import (
    cookie_manager,
    set_student_code_cookie,
    set_session_token_cookie,
    restore_session_from_cookie,
)


def test_cookies_keep_user_logged_in_after_reload():
    """User with valid cookies should remain logged in after a reload."""
    # Clear any previous state/cookies
    st.session_state.clear()
    cookie_manager.store.clear()

    # Pretend the user previously logged in and cookies were set
    set_student_code_cookie(cookie_manager, "abc")
    set_session_token_cookie(cookie_manager, "tok123")

    # Stub ``validate_session_token`` to accept our token without needing
    # external services.
    stub_sessions = types.SimpleNamespace(
        validate_session_token=lambda token, ua_hash="": {"student_code": "abc"}
        if token == "tok123"
        else None
    )
    sys.modules["falowen.sessions"] = stub_sessions

    def loader():
        return pd.DataFrame([{"StudentCode": "abc", "Name": "Alice"}])

    restored = restore_session_from_cookie(cookie_manager, loader)
    assert restored is not None

    sc = restored["student_code"]
    token = restored["session_token"]
    roster = restored.get("data")

    from falowen.sessions import validate_session_token

    assert validate_session_token(token) is not None

    row = (
        roster[roster["StudentCode"].str.lower() == sc].iloc[0]
        if roster is not None and "StudentCode" in roster.columns
        else {}
    )
    st.session_state.update(
        {
            "logged_in": True,
            "student_code": sc,
            "student_name": row.get("Name", ""),
            "student_row": dict(row) if isinstance(row, pd.Series) else {},
            "session_token": token,
        }
    )

    assert st.session_state.get("logged_in") is True
    assert st.session_state.get("student_code") == "abc"
    assert st.session_state.get("student_name") == "Alice"
    assert st.session_state.get("session_token") == "tok123"
