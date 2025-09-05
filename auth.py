# auth.py
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, make_response

import os
import bcrypt


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Safari/iOS-safe refresh-token cookie settings
REFRESH_COOKIE = "refresh_token"
COOKIE_SAMESITE = "Strict"
COOKIE_PATH = "/auth/refresh"
MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Simple in-memory user store with hashed passwords for demo/testing
USERS = {
    "alice@example.com": {
        "id": "alice",
        "password": generate_password_hash("wonderland"),
    }
}

def _set_cookie(resp, token: str):
    """
    Sets the refresh-token cookie. If running under falowen.app, use domain=.falowen.app.
    Otherwise (e.g., testing on <app>.herokuapp.com), omit domain so the cookie is set.
    """
    kwargs = dict(
        max_age=MAX_AGE,
        httponly=True,
        secure=True,                 # requires HTTPS (Cloudflare/Heroku provide this)
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )
    host = (request.host or "").split(":")[0]
    if host.endswith("falowen.app"):
        kwargs["domain"] = ".falowen.app"  # share across www/api if needed

    resp.set_cookie(REFRESH_COOKIE, token, **kwargs)
    return resp

# --- Simple token stubs (replace with real JWT/DB logic) ---
def _issue_access(user_id: str) -> str:
    return f"access_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"

def _issue_refresh(user_id: str) -> str:
    return f"refresh_{user_id}_{int(datetime.now(timezone.utc).timestamp())}"
# ------------------------------------------------------------

def _get_password_hash() -> str:
    """Return the stored bcrypt hash for login validation."""
    return os.environ.get("PASSWORD_HASH", "")


@auth_bp.post("/login")
def login():
    """Authenticate a user.

    Expected JSON body::

        {"email": "name@example.com", "password": "hunter2"}

    Either ``email`` or ``user_id`` may be supplied for the user identifier. Both
    fields are required, otherwise a ``400`` is returned. The supplied password is
    verified against ``PASSWORD_HASH`` using bcrypt. Invalid credentials yield a
    ``401``.
    """


    user_id = data.get("user_id") or data.get("email")
    password = data.get("password")

    if not user_id or not password:
        return jsonify(error="missing credentials"), 400

    stored_hash = _get_password_hash()
    if not stored_hash or not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):

        return jsonify(error="invalid credentials"), 401

    user_id = user.get("id", email)
    access = _issue_access(user_id)
    refresh = _issue_refresh(user_id)

    resp = make_response(jsonify(
        access_token=access,
        refresh_token=refresh,
        expires_in=3600
    ), 200)
    _set_cookie(resp, refresh)   # persist on web via HttpOnly cookie
    return resp

@auth_bp.route("/refresh", methods=["POST", "GET"])
def refresh():
    # Prefer POST body; fall back to cookie (so web + iOS both work)
    body = request.get_json(silent=True) or {}
    rt = body.get("refresh_token") or request.cookies.get(REFRESH_COOKIE)
    if not rt:
        return jsonify(error="missing refresh token"), 401

    # TODO: validate/rotate the refresh token
    access = _issue_access("user")
    new_refresh = rt  # rotate in production

    resp = make_response(jsonify(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=3600
    ), 200)
    _set_cookie(resp, new_refresh)   # extend cookie expiry for web
    return resp

@auth_bp.post("/logout")
def logout():
    resp = make_response("", 204)
    # Clear cookie with the same attributes we set
    kwargs = dict(httponly=True, secure=True, samesite=COOKIE_SAMESITE, path=COOKIE_PATH, max_age=0)
    host = (request.host or "").split(":")[0]
    if host.endswith("falowen.app"):
        kwargs["domain"] = ".falowen.app"
    resp.set_cookie(REFRESH_COOKIE, "", **kwargs)
    return resp
