from http.cookies import SimpleCookie
from email.utils import parsedate_to_datetime
import time

from flask import Flask

from auth import (
    auth_bp,
    MAX_AGE,
    REFRESH_COOKIE,
    COOKIE_PATH,
    COOKIE_SAMESITE,
)


def create_app():
    app = Flask(__name__)
    app.register_blueprint(auth_bp)
    return app


def _cookie_attrs(resp):
    cookie = SimpleCookie()
    cookie.load(resp.headers["Set-Cookie"])
    morsel = cookie[REFRESH_COOKIE]
    return (
        parsedate_to_datetime(morsel["expires"]),
        morsel["path"],
        morsel["samesite"],
        morsel.OutputString(),
    )


def test_refresh_extends_cookie_expiry():
    app = create_app()
    client = app.test_client()

    login_resp = client.post("/auth/login", json={"user_id": "u"})
    first_expires, path, samesite, cookie_header = _cookie_attrs(login_resp)
    assert path == COOKIE_PATH
    assert samesite == COOKIE_SAMESITE

    time.sleep(1)
    refresh_resp1 = client.get("/auth/refresh", headers={"Cookie": cookie_header})
    second_expires, path, samesite, cookie_header2 = _cookie_attrs(refresh_resp1)
    assert path == COOKIE_PATH
    assert samesite == COOKIE_SAMESITE

    time.sleep(1)
    refresh_resp2 = client.get("/auth/refresh", headers={"Cookie": cookie_header2})
    third_expires, path, samesite, _ = _cookie_attrs(refresh_resp2)
    assert path == COOKIE_PATH
    assert samesite == COOKIE_SAMESITE

    assert second_expires > first_expires
    assert third_expires > second_expires
    assert f"max-age={MAX_AGE}" in refresh_resp2.headers["Set-Cookie"].lower()
