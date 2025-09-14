import types, sys
from datetime import UTC, datetime, timedelta

import pytest
from src.auth import st, clear_session_clients, get_session_client

# Stub falowen.sessions before importing module under test
stub_sessions = types.SimpleNamespace(
    refresh_or_rotate_session_token=lambda tok: tok,
    validate_session_token=lambda tok, ua_hash="": {"student_code": "abc"},
)
sys.modules["falowen.sessions"] = stub_sessions

from src.ui.auth import renew_session_if_needed  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_session(monkeypatch):
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "query_params", {})
    clear_session_clients()


def test_token_rotation_updates_state_and_query_param(monkeypatch):
    monkeypatch.setattr(
        stub_sessions, "refresh_or_rotate_session_token", lambda tok: "new"
    )
    st.session_state.update({"session_token": "old", "student_code": "abc"})
    renew_session_if_needed()
    assert st.session_state["session_token"] == "new"
    assert st.query_params["t"] == "new"
    assert get_session_client("new") == "abc"
    assert get_session_client("old") is None
