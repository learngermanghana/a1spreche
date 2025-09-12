import sys
import types
import logging
from datetime import datetime, timedelta, UTC

import streamlit as st

# Stub falowen.sessions before importing module under test
stub_sessions = types.SimpleNamespace(
    create_session_token=lambda *a, **k: "tok",
    destroy_session_token=lambda *a, **k: None,
    refresh_or_rotate_session_token=lambda tok: tok,
    validate_session_token=lambda tok, ua_hash="": {"student_code": "abc"},
)
sys.modules["falowen.sessions"] = stub_sessions

from src.auth import (  # noqa: E402
    SimpleCookieManager,
    set_session_token_cookie,
    clear_session_clients,
    get_session_client,
)
from src.ui.auth import renew_session_if_needed  # noqa: E402


def setup_function(function):
    st.session_state.clear()
    clear_session_clients()


def test_cookie_expiry_refreshed_and_mapping_persisted():
    cm = SimpleCookieManager()
    st.session_state.update(
        {"session_token": "tok123", "student_code": "abc", "cookie_manager": cm}
    )
    set_session_token_cookie(
        cm, "tok123", expires=datetime.now(UTC) + timedelta(days=1)
    )
    old_expiry = cm.store["session_token"]["kwargs"]["expires"]

    renew_session_if_needed()

    new_expiry = cm.store["session_token"]["kwargs"]["expires"]
    assert new_expiry > old_expiry
    assert get_session_client("tok123") == "abc"


def test_token_rotation_updates_state_cookie_and_mapping(monkeypatch):
    cm = SimpleCookieManager()
    st.session_state.update(
        {"session_token": "old", "student_code": "abc", "cookie_manager": cm}
    )
    set_session_token_cookie(cm, "old", expires=datetime.now(UTC) + timedelta(days=1))

    monkeypatch.setattr(
        stub_sessions, "refresh_or_rotate_session_token", lambda tok: "new"
    )

    renew_session_if_needed()

    assert st.session_state["session_token"] == "new"
    assert cm["session_token"] == "new"
    assert get_session_client("new") == "abc"
    assert get_session_client("old") is None

def test_cookie_save_failure_no_error(monkeypatch, caplog):
    class FailingCookieManager(SimpleCookieManager):
        def save(self) -> None:  # pragma: no cover
            raise RuntimeError("boom")

    cm = FailingCookieManager()
    st.session_state.update(
        {"session_token": "tok123", "student_code": "abc", "cookie_manager": cm}
    )
    set_session_token_cookie(cm, "tok123", expires=datetime.now(UTC) + timedelta(days=1))

    called = False

    def fake_toast(msg: str) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("src.ui.auth.toast_err", fake_toast)
    with caplog.at_level(logging.DEBUG):
        renew_session_if_needed()

    assert not called
    assert any(
        r.levelno == logging.DEBUG and "Cookie save failed" in r.message
        for r in caplog.records
    )
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)
