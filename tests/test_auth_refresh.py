import importlib
from flask import Flask

def create_app(monkeypatch):
    """Create a Flask app with the refresh blueprint loaded."""
    import streamlit as st

    # Avoid using real secrets or network during tests
    monkeypatch.setattr(st, "secrets", {}, raising=False)

    import os, sys
    root = os.path.dirname(os.path.dirname(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)
    import falowen.sessions as sessions
    sessions = importlib.reload(sessions)

    app = Flask(__name__)
    app.register_blueprint(sessions.auth_bp)
    return app, sessions


def test_refresh_rotates_token_and_sets_cookie(monkeypatch):
    app, sessions = create_app(monkeypatch)

    # Stub validation and rotation helpers
    monkeypatch.setattr(
        sessions,
        "validate_session_token",
        lambda tok: {"student_code": "u"} if tok == "old" else None,
    )
    monkeypatch.setattr(
        sessions, "refresh_or_rotate_session_token", lambda tok: "new"
    )

    client = app.test_client()
    resp = client.post("/auth/refresh", json={"refresh_token": "old"})
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["refresh_token"] == "new"
    assert "access_token" in data

    cookie = resp.headers["Set-Cookie"]
    assert "session_token=new" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
