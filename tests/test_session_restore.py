import sys
import types

import pandas as pd
import pytest
from src.contracts import is_contract_expired

from src.auth import (
    st,
    create_cookie_manager,
    set_student_code_cookie,
    set_session_token_cookie,
    clear_session,
    restore_session_from_cookie,
    SimpleCookieManager,
    persist_session_client,
    get_session_client,
    clear_session_clients,
    recover_session_from_qp_token,
)
# Stub ``falowen.sessions`` before importing ``src.auth`` to avoid network calls.
stub_sessions = types.SimpleNamespace(validate_session_token=lambda *a, **k: None)
sys.modules.setdefault("falowen.sessions", stub_sessions)

cookie_manager = create_cookie_manager()


@pytest.fixture(autouse=True)
def _reset_session(monkeypatch):
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "query_params", {})
    clear_session_clients()

def test_cookies_keep_user_logged_in_after_reload():
    """User with valid cookies should remain logged in after a reload."""
    # Clear any previous state/cookies
    st.session_state.clear()
    cookie_manager.store.clear()

    # Pretend the user previously logged in and cookies were set
    cookie_manager["student_code"] = "abc"
    cookie_manager["session_token"] = "tok123"

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

def test_session_not_restored_if_contract_expired():
    """Expired contracts should prevent session restoration."""
    st.session_state.clear()
    cookie_manager.store.clear()

    cookie_manager["student_code"] = "abc"
    cookie_manager["session_token"] = "tok123"

    stub_sessions = types.SimpleNamespace(
        validate_session_token=lambda token, ua_hash="": {"student_code": "abc"}
        if token == "tok123"
        else None
    )
    sys.modules["falowen.sessions"] = stub_sessions

    def loader():
        return pd.DataFrame([{"StudentCode": "abc", "ContractEnd": "2020-01-01"}])

    def contract_checker(sc, df):
        row = df[df["StudentCode"] == sc].iloc[0]
        return not is_contract_expired(row)

    restored = restore_session_from_cookie(
        cookie_manager, loader, contract_checker
    )
    assert restored is None
    assert cookie_manager.get("student_code") is None
    assert cookie_manager.get("session_token") is None

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
    cookie_manager["student_code"] = "abc"
    cookie_manager["session_token"] = "tok123"

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


def test_session_rejected_when_user_agent_hash_mismatch():
    """Session restoration fails if the user-agent hash does not match."""

    # Reset state and cookies
    st.session_state.clear()
    cookie_manager.store.clear()

    # Cookies indicate a previous login
    cookie_manager["student_code"] = "abc"
    cookie_manager["session_token"] = "tok123"

    # Stash an incorrect UA hash
    st.session_state["__ua_hash"] = "wrong_hash"

    # Stub validation to require a specific UA hash
    stub_sessions = types.SimpleNamespace(
        validate_session_token=lambda tok, ua_hash="": {"student_code": "abc"}
        if tok == "tok123" and ua_hash == "correct_hash"
        else None
    )
    sys.modules["falowen.sessions"] = stub_sessions

    # Restoration should fail because ua_hash mismatch
    assert restore_session_from_cookie(cookie_manager) is None



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
    cookie_manager["student_code"] = "abc"
    cookie_manager["session_token"] = "tok123"

    # Logout sequence
    destroy_session_token(st.session_state["session_token"])
    clear_session(cookie_manager)
    st.session_state["session_token"] = ""

    # No cookies should remain and token was revoked
    assert cookie_manager.get("student_code") is None
    assert cookie_manager.get("session_token") is None
    assert destroyed == ["tok123"]
    assert restore_session_from_cookie(cookie_manager) is None


def test_token_query_param_recreates_cookies(monkeypatch):
    """Missing cookies but ``?t=`` query param should recreate them."""
    st.session_state.clear()
    cookie_manager.store.clear()
    clear_session_clients()
    st.session_state["cookie_manager"] = cookie_manager
    st.query_params.clear()
    st.query_params["t"] = "tok123"

    stub_sessions = types.SimpleNamespace(
        validate_session_token=lambda tok, ua_hash="": {"student_code": "abc"}
        if tok == "tok123"
        else None
    )
    sys.modules["falowen.sessions"] = stub_sessions

    monkeypatch.setattr(st, "rerun", lambda: None)

    recover_session_from_qp_token()

    assert cookie_manager.get("session_token") == "tok123"
    assert cookie_manager.get("student_code") == "abc"
    assert get_session_client("tok123") == "abc"
    assert "t" not in st.query_params


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
    cookie_manager["student_code"] = "old"
    cookie_manager["session_token"] = "tok_old"

    # User logs in as different student
    destroy_session_token(st.session_state.get("session_token"))
    clear_session(cookie_manager)
    st.session_state["session_token"] = "tok_new"
    cookie_manager["student_code"] = "new"
    cookie_manager["session_token"] = "tok_new"

    assert destroyed == ["tok_old"]
    assert cookie_manager.get("student_code") == "new"
    assert cookie_manager.get("session_token") == "tok_new"

def test_clear_session_requires_explicit_save():
    """clear_session removes cookies but does not save automatically."""

    class TrackingCookieManager(SimpleCookieManager):
        def __init__(self):  # pragma: no cover - trivial
            super().__init__()
            self.saved = False

        def save(self):  # pragma: no cover - trivial
            self.saved = True

    cm = TrackingCookieManager()
    cm["student_code"] = "abc"
    cm["session_token"] = "tok123"
    clear_session(cm)

    assert cm.get("student_code") is None
    assert cm.get("session_token") is None
    assert cm.saved is False

    cm.save()
    assert cm.saved is True


def test_cookie_functions_require_manual_save():
    """Setting cookies requires a single explicit save."""

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
    assert cm.save_calls == 0

    cm.save()
    assert cm.save_calls == 1

def test_cookie_functions_apply_defaults_and_allow_override():
    """Cookies should include secure defaults but allow overriding."""

    cm = SimpleCookieManager()
    set_student_code_cookie(cm, "abc")
    set_session_token_cookie(cm, "tok123", secure=False, samesite="Lax")

    
    # ``get`` should return the stored values even though the manager keeps
    # additional metadata about the cookie options.
    assert cm.get("student_code") == "abc"
    assert cm.get("session_token") == "tok123"

    student_kwargs = cm.store["student_code"]["kwargs"]
    token_kwargs = cm.store["session_token"]["kwargs"]

    assert student_kwargs == {
        "httponly": True,
        "secure": True,
        "samesite": "Lax",
        "domain": ".falowen.app",
    }
    assert token_kwargs["httponly"] is True
    assert token_kwargs["secure"] is False
    assert token_kwargs["samesite"] == "Lax"
    assert token_kwargs["domain"] == ".falowen.app"

def test_multiple_cookie_managers_are_isolated():
    """Cookies set on different managers should not leak between sessions."""

    cm1 = create_cookie_manager()
    cm2 = create_cookie_manager()

    cm1["student_code"] = "stuA"
    cm1["session_token"] = "tokA"

    cm2["student_code"] = "stuB"
    cm2["session_token"] = "tokB"

    assert cm1.get("student_code") == "stuA"
    assert cm1.get("session_token") == "tokA"
    assert cm2.get("student_code") == "stuB"
    assert cm2.get("session_token") == "tokB"

    clear_session(cm1)

    assert cm1.get("student_code") is None
    assert cm2.get("student_code") == "stuB"


def test_obsolete_cookie_triggers_login_flow(monkeypatch):
    """If cookie student code is missing from roster, session is cleared."""
    import sys
    import types
    import pandas as pd
    import streamlit as st

    st.session_state.clear()

    # Prepare cookie with obsolete student code
    cm = create_cookie_manager()
    cm["student_code"] = "ghost"
    cm["session_token"] = "tok123"

    # Stub external dependencies required by a1sprechen import
    monkeypatch.setitem(sys.modules, "docx", types.SimpleNamespace(Document=type("Doc", (), {})))
    monkeypatch.setitem(
        sys.modules,
        "firebase_admin",
        types.SimpleNamespace(credentials=types.SimpleNamespace(), firestore=types.SimpleNamespace, messaging=types.SimpleNamespace()),
    )
    firestore_v1 = types.SimpleNamespace(FieldFilter=type("FF", (), {}))
    cloud = types.SimpleNamespace(firestore_v1=firestore_v1)
    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(cloud=cloud, api_core=None))
    monkeypatch.setitem(sys.modules, "google.cloud", cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.firestore_v1", firestore_v1)
    api_core_ex = types.SimpleNamespace(GoogleAPICallError=Exception)
    monkeypatch.setitem(sys.modules, "google.api_core", types.SimpleNamespace(exceptions=api_core_ex))
    monkeypatch.setitem(sys.modules, "google.api_core.exceptions", api_core_ex)
    monkeypatch.setitem(sys.modules, "fpdf", types.SimpleNamespace(FPDF=type("PDF", (), {})))
    monkeypatch.setitem(sys.modules, "gtts", types.SimpleNamespace(gTTS=type("gTTS", (), {})))

    class DummyOpenAI:
        def __init__(self, api_key=None, **kwargs):
            pass

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyOpenAI))
    monkeypatch.setitem(sys.modules, "streamlit_quill", types.SimpleNamespace(st_quill=lambda *a, **k: None))

    # Stub internal modules that might touch networks during import
    sys.modules["src.session_management"] = types.SimpleNamespace(
        bootstrap_state=lambda: None,
        determine_level=lambda sc, row: "A1",
        ensure_student_level=lambda: None,
    )
    sys.modules["src.stats"] = types.SimpleNamespace(
        get_student_level=lambda sc: "A1",
        get_vocab_stats=lambda sc: {},
        save_vocab_attempt=lambda *a, **k: None,
        vocab_attempt_exists=lambda *a, **k: False,
    )
    sys.modules["src.ui_components"] = types.SimpleNamespace(
        render_assignment_reminder=lambda *a, **k: None,
        render_link=lambda *a, **k: None,
        render_vocab_lookup=lambda *a, **k: None,
    )
    sys.modules["src.assignment_ui"] = types.SimpleNamespace(
        load_assignment_scores=lambda *a, **k: None,
        render_results_and_resources_tab=lambda *a, **k: None,
        get_assignment_summary=lambda *a, **k: None,
    )
    sys.modules["src.stats_ui"] = types.SimpleNamespace(
        render_vocab_stats=lambda *a, **k: None,
        render_schreiben_stats=lambda *a, **k: None,
    )
    sys.modules["src.schreiben"] = types.SimpleNamespace(
        update_schreiben_stats=lambda *a, **k: None,
        get_schreiben_stats=lambda *a, **k: None,
        save_submission=lambda *a, **k: None,
        save_schreiben_feedback=lambda *a, **k: None,
        load_schreiben_feedback=lambda *a, **k: None,
        delete_schreiben_feedback=lambda *a, **k: None,
    )
    sys.modules["src.group_schedules"] = types.SimpleNamespace(
        load_group_schedules=lambda *a, **k: None
    )
    sys.modules["src.schedule"] = types.SimpleNamespace(
        load_level_schedules=lambda *a, **k: None,
        get_level_schedules=lambda *a, **k: None,
    )
    sys.modules["src.ui_helpers"] = types.SimpleNamespace(
        qp_get=lambda *a, **k: None,
        qp_clear=lambda *a, **k: None,
        qp_clear_keys=lambda *a, **k: None,
        seed_falowen_state_from_qp=lambda: None,
        highlight_terms=lambda *a, **k: None,
        filter_matches=lambda *a, **k: None,
    )

    # Patch config and session helpers
    sys.modules["src.config"] = types.SimpleNamespace(
        get_cookie_manager=lambda: cm,
        SB_SESSION_TARGET="",
    )

    sys.modules["falowen.sessions"] = types.SimpleNamespace(
        db=None,
        create_session_token=lambda *a, **k: None,
        destroy_session_token=lambda *a, **k: None,
        api_get=lambda *a, **k: None,
        api_post=lambda *a, **k: None,
        validate_session_token=lambda tok, ua_hash="": {"student_code": "ghost"},
    )

    import src.data_loading as data_loading

    data_loading.load_student_data = lambda: pd.DataFrame([
        {"StudentCode": "abc", "Name": "Alice"}
    ])

    import src.session_management as session_management

    session_management.determine_level = lambda sc, row: "A1"

    monkeypatch.setenv("OPENAI_API_KEY", "test")

    # Ensure st.stop halts execution without running rest of app
    import streamlit as st
    monkeypatch.setattr(st, "stop", lambda: (_ for _ in ()).throw(SystemExit))

    # Import app; it should clear cookies and raise SystemExit from st.stop
    try:
        import a1sprechen  # noqa: F401
    except SystemExit:
        pass

    assert cm.get("student_code") is None
    assert cm.get("session_token") is None
    assert st.session_state.get("logged_in", False) is False
