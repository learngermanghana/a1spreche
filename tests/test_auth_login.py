import importlib
from flask import Flask
import bcrypt


def _create_app(monkeypatch, password: str = "secret"):
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    monkeypatch.setenv("PASSWORD_HASH", hashed)
    module = importlib.import_module("auth")
    app = Flask(__name__)
    app.register_blueprint(module.auth_bp)
    return app


def test_login_success(monkeypatch):
    app = _create_app(monkeypatch)
    client = app.test_client()
    resp = client.post("/auth/login", json={"email": "user", "password": "secret"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data and "refresh_token" in data


def test_login_missing_fields(monkeypatch):
    app = _create_app(monkeypatch)
    client = app.test_client()
    resp = client.post("/auth/login", json={"email": "user"})
    assert resp.status_code == 400


def test_login_bad_password(monkeypatch):
    app = _create_app(monkeypatch)
    client = app.test_client()
    resp = client.post("/auth/login", json={"email": "user", "password": "wrong"})
    assert resp.status_code == 401
