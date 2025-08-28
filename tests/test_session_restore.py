import sys
import types

import pandas as pd
import streamlit as st

# Stub ``falowen.sessions`` before importing ``src.auth`` to avoid network calls.
stub_sessions = types.SimpleNamespace(validate_session_token=lambda *a, **k: None)
sys.modules.setdefault("falowen.sessions", stub_sessions)

from src.auth import (
    create_cookie_manager,
    set_student_code_cookie,
    set_session_token_cookie,
    clear_session,
    restore_session_from_cookie,
    SimpleCookieManager,
    persist_session_client,
    get_session_client,
    clear_session_clients,
)

cookie_manager = create_cookie_manager()

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
    import src.auth as auth_module
    auth_module.validate_session_token = stub_sessions.validate_session_token

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

def test_persist_session_client_roundtrip():
    """persist_session_client should store and retrieve mappings thread safely."""
    clear_session_clients()
    persist_session_client("tok1", "stu1")
    assert get_session_client("tok1") == "stu1"

def test_session_not_restored_when_student_code_mismatch():
    """User is not logged in if token validation returns a different code."""
    # Reset state and cookies
    st.session_state.clear()
    cookie_manager.store.clear()

    # Cookies indicate a previous login
    set_student_code_cookie(cookie_manager, "abc")
    set_session_token_cookie(cookie_manager, "tok123")

    # Stub validation to return a *different* student code
    called: list[str] = []

    def _validate(token: str, ua_hash: str = ""):
        called.append(token)
        return {"student_code": "xyz"} if token == "tok123" else None

    stub_sessions = types.SimpleNamespace(validate_session_token=_validate)
    sys.modules["falowen.sessions"] = stub_sessions
    import src.auth as auth_module
    auth_module.validate_session_token = stub_sessions.validate_session_token

    def loader():
        return pd.DataFrame([{"StudentCode": "abc", "Name": "Alice"}])

    restored = restore_session_from_cookie(cookie_manager, loader)
    assert restored is None

    # ``validate_session_token`` should still have been called
    assert called == ["tok123"]
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

def test_cookie_functions_apply_defaults_and_allow_override():
    """Cookies should include secure defaults but allow overriding."""

    class RecordingCookieManager(SimpleCookieManager):
        def set(self, key: str, value: str, **kwargs):  # pragma: no cover - trivial
            self.store[key] = {"value": value, "kwargs": kwargs}

    cm = RecordingCookieManager()
    set_student_code_cookie(cm, "abc")
    set_session_token_cookie(cm, "tok123", secure=False, samesite="Lax")

    student_kwargs = cm.store["student_code"]["kwargs"]
    token_kwargs = cm.store["session_token"]["kwargs"]

    assert student_kwargs == {"httponly": True, "secure": True, "samesite": "Strict"}
    assert token_kwargs["httponly"] is True
    assert token_kwargs["secure"] is False
    assert token_kwargs["samesite"] == "Lax"

def test_multiple_cookie_managers_are_isolated():
    """Cookies set on different managers should not leak between sessions."""

    cm1 = create_cookie_manager()
    cm2 = create_cookie_manager()

    set_student_code_cookie(cm1, "stuA")
    set_session_token_cookie(cm1, "tokA")

    set_student_code_cookie(cm2, "stuB")
    set_session_token_cookie(cm2, "tokB")

    assert cm1.get("student_code") == "stuA"
    assert cm1.get("session_token") == "tokA"
    assert cm2.get("student_code") == "stuB"
    assert cm2.get("session_token") == "tokB"

    clear_session(cm1)

    assert cm1.get("student_code") is None
    assert cm2.get("student_code") == "stuB"
