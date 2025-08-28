import sys
import types

import pandas as pd
import streamlit as st

from src.auth import (
    set_student_code_cookie,
    set_session_token_cookie,
    clear_session,
    restore_session_from_cookie,
    SimpleCookieManager,
    bootstrap_cookies,
)

# Each test operates on its own in-memory cookie manager
cookie_manager = bootstrap_cookies(SimpleCookieManager())

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
    # Stub ``get_student_level`` to avoid network calls
    orig_stats = sys.modules.get("src.stats")
    stub_stats = types.SimpleNamespace(get_student_level=lambda sc: "B2")
    sys.modules["src.stats"] = stub_stats
    from src.stats import get_student_level

    level = row.get("Level") or get_student_level(sc)
    st.session_state.update(
        {
            "logged_in": True,
            "student_code": sc,
            "student_name": row.get("Name", ""),
            "student_row": dict(row) if isinstance(row, pd.Series) else {},
            "session_token": token,
            "student_level": level,
        }
    )
    if orig_stats is not None:
        sys.modules["src.stats"] = orig_stats
    else:
        sys.modules.pop("src.stats")

    assert st.session_state.get("logged_in") is True
    assert st.session_state.get("student_code") == "abc"
    assert st.session_state.get("student_name") == "Alice"
    assert st.session_state.get("session_token") == "tok123"
    assert st.session_state.get("student_level") == "B2"

def test_session_not_restored_when_student_code_mismatch():
    """User is not logged in if token validation returns a different code."""
    # Reset state and cookies
    st.session_state.clear()
    cookie_manager.store.clear()

    # Cookies indicate a previous login
    set_student_code_cookie(cookie_manager, "abc")
    set_session_token_cookie(cookie_manager, "tok123")

    # Stub validation to return a *different* student code
    stub_sessions = types.SimpleNamespace(
        validate_session_token=lambda token, ua_hash="": {"student_code": "xyz"}
        if token == "tok123"
        else None
    )
    sys.modules["falowen.sessions"] = stub_sessions

    def loader():
        return pd.DataFrame([{"StudentCode": "abc", "Name": "Alice"}])

    restored = restore_session_from_cookie(cookie_manager, loader)
    assert restored is not None

    # Validate session token but do not log in because codes don't match
    from falowen.sessions import validate_session_token

    validated = validate_session_token(restored["session_token"])
    assert validated is not None
    assert validated.get("student_code") != restored["student_code"]

    if validated.get("student_code") == restored["student_code"]:
        st.session_state["logged_in"] = True

    assert st.session_state.get("logged_in", False) is False



def test_logout_clears_cookies_and_revokes_token():
    """Logging out removes cookies and revokes the session token."""
    st.session_state.clear()
    cookie_manager.store.clear()

    destroyed: list[str] = []

    stub_sessions = types.SimpleNamespace(
        destroy_session_token=lambda tok: destroyed.append(tok)
    )
    sys.modules["falowen.sessions"] = stub_sessions
    from falowen.sessions import destroy_session_token

    # Simulate an active session
    st.session_state["session_token"] = "tok123"
    set_student_code_cookie(cookie_manager, "abc")
    set_session_token_cookie(cookie_manager, "tok123")

    # Logout sequence
    destroy_session_token(st.session_state["session_token"])
    clear_session(cookie_manager)
    st.session_state["session_token"] = ""

    # No cookies should remain and token was revoked
    assert cookie_manager.get("student_code") is None
    assert cookie_manager.get("session_token") is None
    assert destroyed == ["tok123"]
    assert restore_session_from_cookie(cookie_manager) is None


def test_relogin_replaces_session_and_clears_old_token():
    """Re-login on the same machine should revoke previous token and set new cookies."""
    st.session_state.clear()
    cookie_manager.store.clear()

    destroyed: list[str] = []
    stub_sessions = types.SimpleNamespace(
        destroy_session_token=lambda tok: destroyed.append(tok)
    )
    sys.modules["falowen.sessions"] = stub_sessions
    from falowen.sessions import destroy_session_token

    # Existing login (old user)
    st.session_state["session_token"] = "tok_old"
    set_student_code_cookie(cookie_manager, "old")
    set_session_token_cookie(cookie_manager, "tok_old")

    # User logs in as different student
    destroy_session_token(st.session_state.get("session_token"))
    clear_session(cookie_manager)
    st.session_state["session_token"] = "tok_new"
    set_student_code_cookie(cookie_manager, "new")
    set_session_token_cookie(cookie_manager, "tok_new")

    assert destroyed == ["tok_old"]
    assert cookie_manager.get("student_code") == "new"
    assert cookie_manager.get("session_token") == "tok_new"

def test_clear_session_persists_cookie_deletion():
    """clear_session should persist deletions so cookies do not linger."""

    class TrackingCookieManager(SimpleCookieManager):
        def __init__(self):  # pragma: no cover - trivial
            super().__init__()
            self.saved = False

        def save(self):  # pragma: no cover - trivial
            self.saved = True

    cm = TrackingCookieManager()
    set_student_code_cookie(cm, "abc")
    set_session_token_cookie(cm, "tok123")
    clear_session(cm)

    assert cm.get("student_code") is None
    assert cm.get("session_token") is None
    assert cm.saved is True

def test_set_cookie_functions_persist_changes():
    """Setting cookies should call save so values persist across reloads."""

    class TrackingCookieManager(SimpleCookieManager):
        def __init__(self):  # pragma: no cover - trivial
            super().__init__()
            self.save_calls: int = 0

        def save(self):  # pragma: no cover - trivial
            self.save_calls += 1

    cm = TrackingCookieManager()
    set_student_code_cookie(cm, "abc")
    set_session_token_cookie(cm, "tok123")

    assert cm.get("student_code") == "abc"
    assert cm.get("session_token") == "tok123"
    assert cm.save_calls >= 2

def test_cookie_managers_are_isolated_between_devices():
    """Each device keeps its own cookies without leaking to others."""

    cm_a = SimpleCookieManager()
    cm_b = SimpleCookieManager()

    # Device A logs in as first student
    set_student_code_cookie(cm_a, "stu_a")
    set_session_token_cookie(cm_a, "tok_a")

    # Ensure device B is still empty
    assert cm_b.get("student_code") is None
    assert cm_b.get("session_token") is None

    # Device B logs in as another student
    set_student_code_cookie(cm_b, "stu_b")
    set_session_token_cookie(cm_b, "tok_b")

    # Restore sessions from cookies for both devices
    restored_a = restore_session_from_cookie(cm_a)
    restored_b = restore_session_from_cookie(cm_b)

    # Each cookie manager should retain its own data only
    assert restored_a["student_code"] == "stu_a"
    assert restored_a["session_token"] == "tok_a"
    assert restored_b["student_code"] == "stu_b"
    assert restored_b["session_token"] == "tok_b"

    # No cross-contamination between devices
    assert cm_a.get("student_code") != cm_b.get("student_code")
    assert cm_a.get("session_token") != cm_b.get("session_token")
