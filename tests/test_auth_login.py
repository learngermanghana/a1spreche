from http.cookies import SimpleCookie
from flask import Flask

import auth


def create_app():
    app = Flask(__name__)
    app.register_blueprint(auth.auth_bp)
    return app


def test_login_success():
    app = create_app()
    client = app.test_client()
    resp = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wonderland"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert data["refresh_token"]
    cookie = SimpleCookie()
    cookie.load(resp.headers["Set-Cookie"])
    assert cookie["refresh_token"].value == data["refresh_token"]


def test_login_failure():
    app = create_app()
    client = app.test_client()
    resp = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401
