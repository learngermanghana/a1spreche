import json
import os
from importlib import reload
import sys
from pathlib import Path
import uuid

import jwt
from flask import Flask
from werkzeug.security import generate_password_hash

sys.path.append(str(Path(__file__).resolve().parents[1]))
import auth


TEST_SECRET = "test-secret"
TEST_HASHES = {"u": generate_password_hash("pw")}


def _configure_env() -> None:
    os.environ["JWT_SECRET"] = TEST_SECRET
    os.environ["AUTH_USER_CREDENTIALS"] = json.dumps(TEST_HASHES)
    db_path = Path(__file__).resolve().parent / f"refresh_tokens_{uuid.uuid4().hex}.db"
    # Ensure a clean database for every test run.
    if db_path.exists():
        db_path.unlink()
    os.environ["REFRESH_DB_PATH"] = str(db_path)


def create_app():
    _configure_env()
    reload(auth)
    app = Flask(__name__)
    app.register_blueprint(auth.auth_bp)
    return app


def _https_client(app: Flask):
    client = app.test_client()
    client.environ_base["wsgi.url_scheme"] = "https"
    return client


def test_login_issues_tokens():
    app = create_app()
    client = _https_client(app)

    # invalid credentials rejected
    bad = client.post("/auth/login", json={"user_id": "u", "password": "bad"})
    assert bad.status_code == 401

    resp = client.post("/auth/login", json={"user_id": "u", "password": "pw"})
    data = resp.get_json()
    assert resp.status_code == 200
    assert "access_token" in data and "refresh_token" in data

    decoded = jwt.decode(data["access_token"], auth.JWT_SECRET, algorithms=[auth.JWT_ALG])
    assert decoded["sub"] == "u"


def test_refresh_rotates_and_rejects_old():
    app = create_app()
    client = _https_client(app)

    login = client.post("/auth/login", json={"user_id": "u", "password": "pw"}).get_json()
    old_refresh = login["refresh_token"]

    r1 = client.post("/auth/refresh", json={"refresh_token": old_refresh}).get_json()
    new_refresh = r1["refresh_token"]
    assert new_refresh != old_refresh

    r2 = client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401


def test_logout_revokes_refresh_token():
    app = create_app()
    client = _https_client(app)

    login_resp = client.post("/auth/login", json={"user_id": "u", "password": "pw"})
    cookie = login_resp.headers["Set-Cookie"]

    logout_resp = client.post("/auth/logout", headers={"Cookie": cookie})
    assert logout_resp.status_code == 204

    refresh_resp = client.get("/auth/refresh", headers={"Cookie": cookie})
    assert refresh_resp.status_code == 401


def test_multiple_browsers_keep_sessions_active():
    app = create_app()
    client_a = _https_client(app)
    client_b = _https_client(app)

    login_a = client_a.post("/auth/login", json={"user_id": "u", "password": "pw"}).get_json()
    refresh_a = login_a["refresh_token"]

    login_b = client_b.post("/auth/login", json={"user_id": "u", "password": "pw"}).get_json()
    refresh_b = login_b["refresh_token"]

    assert refresh_a != refresh_b

    resp_a = client_a.post("/auth/refresh", json={"refresh_token": refresh_a})
    resp_b = client_b.post("/auth/refresh", json={"refresh_token": refresh_b})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200


def test_logout_only_clears_current_token():
    app = create_app()
    client_a = _https_client(app)
    client_b = _https_client(app)

    login_a = client_a.post("/auth/login", json={"user_id": "u", "password": "pw"}).get_json()
    refresh_a = login_a["refresh_token"]

    login_b_resp = client_b.post("/auth/login", json={"user_id": "u", "password": "pw"})
    refresh_b = login_b_resp.get_json()["refresh_token"]
    cookie_b = login_b_resp.headers["Set-Cookie"]

    logout_b = client_b.post("/auth/logout", headers={"Cookie": cookie_b})
    assert logout_b.status_code == 204

    still_valid = client_a.post("/auth/refresh", json={"refresh_token": refresh_a})
    assert still_valid.status_code == 200

    revoked = client_b.post("/auth/refresh", json={"refresh_token": refresh_b})
    assert revoked.status_code == 401
