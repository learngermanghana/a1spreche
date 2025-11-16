import json
import os
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from email.utils import parsedate_to_datetime
import time

from flask import Flask
from importlib import reload
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash

sys.path.append(str(Path(__file__).resolve().parents[1]))
import auth


TEST_SECRET = "test-secret"
TEST_HASHES = {"u": generate_password_hash("pw")}


def _configure_env(*, max_age_days: int | None = None) -> None:
    os.environ["JWT_SECRET"] = TEST_SECRET
    os.environ["AUTH_USER_CREDENTIALS"] = json.dumps(TEST_HASHES)
    if max_age_days is None:
        os.environ.pop("SESSION_MAX_AGE_DAYS", None)
    else:
        os.environ["SESSION_MAX_AGE_DAYS"] = str(max_age_days)


def create_app(*, max_age_days: int | None = None):
    _configure_env(max_age_days=max_age_days)
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


def test_cookie_max_age_override():
    override_days = 120
    app = create_app(max_age_days=override_days)
    client = app.test_client()

    login_resp = client.post("/auth/login", json={"user_id": "u", "password": "pw"})
    expires, cookie_header = _cookie_expires(login_resp)

    assert auth.MAX_AGE == override_days * 24 * 60 * 60
    assert f"max-age={auth.MAX_AGE}" in cookie_header.lower()

    delta = expires - datetime.now(timezone.utc)
    assert abs(delta.total_seconds() - auth.MAX_AGE) < 5
