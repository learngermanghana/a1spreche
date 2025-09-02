from http.cookies import SimpleCookie
from email.utils import parsedate_to_datetime

from flask import Flask

from auth import auth_bp, MAX_AGE


def create_app():
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    return app


def _cookie_expires(resp):
    cookie = SimpleCookie()
    cookie.load(resp.headers["Set-Cookie"])
    return parsedate_to_datetime(cookie["session"]["expires"]), cookie["session"].OutputString()


def test_refresh_extends_cookie_expiry():
    app = create_app()
    client = app.test_client()

    login_resp = client.post("/auth/login", json={"user_id": "u"})
    first_expires, cookie_header = _cookie_expires(login_resp)

    refresh_resp1 = client.get("/auth/refresh", headers={"Cookie": cookie_header})
    second_expires, cookie_header2 = _cookie_expires(refresh_resp1)

    refresh_resp2 = client.get("/auth/refresh", headers={"Cookie": cookie_header2})
    third_expires, _ = _cookie_expires(refresh_resp2)

    assert second_expires > first_expires
    assert third_expires > second_expires
    assert f"max-age={MAX_AGE}" in refresh_resp2.headers["Set-Cookie"].lower()
