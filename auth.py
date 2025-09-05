# auth.py
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, make_response
import os
import jwt
import uuid

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

COOKIE_NAME = "session"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")  # use "None" if cross-site; requires HTTPS
COOKIE_PATH = "/"
MAX_AGE = 60 * 60 * 24 * 30  # 30 days

def _set_cookie(resp, token: str):
    """
    Sets the session cookie. If running under falowen.app, use domain=.falowen.app.
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

    resp.set_cookie(COOKIE_NAME, token, **kwargs)
    return resp

# --- Simple in-memory user store and JWT helpers ---
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
ACCESS_TTL = 3600

USERS = {
    "u": {"password": "pw", "refresh": None},
}


def _issue_access(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(seconds=ACCESS_TTL)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def _issue_refresh(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(seconds=MAX_AGE),
        "iat": datetime.utcnow(),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    USERS.setdefault(user_id, {}).update({"refresh": token})
    return token


def _get_user_from_refresh(token: str) -> str | None:
    """Validate refresh token and return user_id if valid, else None."""
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        if data.get("type") != "refresh":
            raise jwt.InvalidTokenError("not refresh")
        user_id = data["sub"]
    except jwt.PyJWTError:
        return None

    stored = USERS.get(user_id, {}).get("refresh")
    if stored != token:
        # Revoke mismatched token
        if user_id in USERS:
            USERS[user_id]["refresh"] = None
        return None
    return user_id
# ------------------------------------------------------------

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or data.get("email")
    password = data.get("password") or data.get("pw")
    if not user_id or user_id not in USERS or USERS[user_id]["password"] != password:
        return jsonify(error="invalid credentials"), 401

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
    rt = body.get("refresh_token") or request.cookies.get(COOKIE_NAME)
    if not rt:
        return jsonify(error="missing refresh token"), 401

    user_id = _get_user_from_refresh(rt)
    if not user_id:
        return jsonify(error="invalid refresh token"), 401

    access = _issue_access(user_id)
    new_refresh = _issue_refresh(user_id)

    resp = make_response(jsonify(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=3600
    ), 200)
    _set_cookie(resp, new_refresh)   # extend cookie expiry for web
    return resp

@auth_bp.post("/logout")
def logout():
    rt = request.cookies.get(COOKIE_NAME)
    if rt:
        uid = _get_user_from_refresh(rt)
        if uid and uid in USERS:
            USERS[uid]["refresh"] = None

    resp = make_response("", 204)
    # Clear cookie with the same attributes we set
    kwargs = dict(httponly=True, secure=True, samesite=COOKIE_SAMESITE, path=COOKIE_PATH, max_age=0)
    host = (request.host or "").split(":")[0]
    if host.endswith("falowen.app"):
        kwargs["domain"] = ".falowen.app"
    resp.set_cookie(COOKIE_NAME, "", **kwargs)
    return resp
