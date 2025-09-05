"""Tests for the /auth/refresh endpoint in falowen.sessions."""

from http.cookies import SimpleCookie
import importlib
import sys
import types

from flask import Flask


def _create_app(monkeypatch):
    """Create a Flask app with the sessions blueprint registered.

    External dependencies used by ``falowen.sessions`` are stubbed so the
    module can be imported without hitting network services.
    """

    firebase_admin_stub = types.ModuleType("firebase_admin")
    firebase_admin_stub._apps = []
    firebase_admin_stub.initialize_app = lambda *a, **k: None
    credentials_stub = types.ModuleType("firebase_admin.credentials")
    credentials_stub.Certificate = lambda *a, **k: None
    firestore_stub = types.ModuleType("firebase_admin.firestore")
    firestore_stub.client = lambda: object()
    firebase_admin_stub.credentials = credentials_stub
    firebase_admin_stub.firestore = firestore_stub

    monkeypatch.setitem(sys.modules, "firebase_admin", firebase_admin_stub)
    monkeypatch.setitem(sys.modules, "firebase_admin.credentials", credentials_stub)
    monkeypatch.setitem(sys.modules, "firebase_admin.firestore", firestore_stub)

    streamlit_stub = types.ModuleType("streamlit")
    streamlit_stub.secrets = {"firebase": {}}
    streamlit_stub.error = lambda *a, **k: None
    streamlit_stub.session_state = {}
    monkeypatch.setitem(sys.modules, "streamlit", streamlit_stub)

    sys.modules.pop("falowen.sessions", None)
    sessions = importlib.import_module("falowen.sessions")
    # Ensure module entry is restored after test
    monkeypatch.setitem(sys.modules, "falowen.sessions", sessions)

    app = Flask(__name__)
    app.register_blueprint(sessions.auth_bp)
    return app, sessions


def test_refresh_rotates_token_and_sets_cookie(monkeypatch):
    app, sessions = _create_app(monkeypatch)
    client = app.test_client()

    calls: dict[str, str] = {}

    def validate(tok, ua_hash=""):
        calls["validate"] = tok
        return {"student_code": "abc"}

    def rotate(tok):
        calls["rotate"] = tok
        return "newtoken"

    monkeypatch.setattr(sessions, "validate_session_token", validate)
    monkeypatch.setattr(sessions, "refresh_or_rotate_session_token", rotate)

    resp = client.post("/auth/refresh", json={"refresh_token": "oldtoken"})
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["refresh_token"] == "newtoken"
    assert "access_token" in data

    cookie = SimpleCookie()
    cookie.load(resp.headers["Set-Cookie"])
    morsel = cookie["session_token"]
    assert morsel.value == "newtoken"
    assert morsel["path"] == "/"
    assert morsel["samesite"] == "Strict"
    header = morsel.OutputString()
    assert "HttpOnly" in header and "Secure" in header

    assert calls["validate"] == "oldtoken"
    assert calls["rotate"] == "oldtoken"


def test_refresh_missing_token(monkeypatch):
    app, sessions = _create_app(monkeypatch)
    client = app.test_client()

    resp = client.post("/auth/refresh", json={})
    assert resp.status_code == 401
