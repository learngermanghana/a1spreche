from http.cookies import SimpleCookie
from email.utils import parsedate_to_datetime
import time

from flask import Flask
from importlib import reload
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import auth


def create_app():
    reload(auth)
    app = Flask(__name__)
    app.register_blueprint(auth.auth_bp)
    return app


def _cookie_expires(resp):
    cookie = SimpleCookie()
    cookie.load(resp.headers["Set-Cookie"])
    return parsedate_to_datetime(cookie["session"]["expires"]), cookie["session"].OutputString()


def test_refresh_extends_cookie_expiry():
    app = create_app()
    client = app.test_client()

    login_resp = client.post("/auth/login", json={"user_id": "u", "password": "pw"})
    first_expires, cookie_header = _cookie_expires(login_resp)

    time.sleep(1)
    refresh_resp1 = client.get("/auth/refresh", headers={"Cookie": cookie_header})
    second_expires, cookie_header2 = _cookie_expires(refresh_resp1)

    time.sleep(1)
    refresh_resp2 = client.get("/auth/refresh", headers={"Cookie": cookie_header2})
    third_expires, _ = _cookie_expires(refresh_resp2)

    assert second_expires > first_expires
    assert third_expires > second_expires
    assert f"max-age={auth.MAX_AGE}" in refresh_resp2.headers["Set-Cookie"].lower()
