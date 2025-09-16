# auth.py
from datetime import UTC, datetime, timedelta
from flask import Blueprint, request, jsonify, make_response
import json
import os
import jwt
import uuid
import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash

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

# --- JWT helpers and refresh-token persistence ---
_DEFAULT_JWT_SECRET = "dev-secret"
_PRODUCTION_VALUES = {"prod", "production", "live"}
_ENV_NAMES = ("AUTH_ENV", "APP_ENV", "ENV", "FLASK_ENV", "PYTHON_ENV", "STREAMLIT_ENV")


def _is_production_env() -> bool:
    for name in _ENV_NAMES:
        value = os.getenv(name)
        if value and value.strip().lower() in _PRODUCTION_VALUES:
            return True
    return os.getenv("AUTH_FORCE_PRODUCTION", "").strip().lower() in {"1", "true", "yes", "on"}


def _load_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        if secret == _DEFAULT_JWT_SECRET and _is_production_env():
            raise RuntimeError("JWT_SECRET must not use the default value in production.")
        return secret

    if _is_production_env():
        raise RuntimeError("JWT_SECRET environment variable is required in production.")

    return _DEFAULT_JWT_SECRET


JWT_SECRET = _load_jwt_secret()
JWT_ALG = "HS256"
ACCESS_TTL = 3600

_CREDENTIALS_ENV = "AUTH_USER_CREDENTIALS"
_CREDENTIALS_FILE_ENV = "AUTH_USER_CREDENTIALS_FILE"


def _load_user_credentials() -> dict[str, str]:
    raw = os.getenv(_CREDENTIALS_ENV)
    creds_path = os.getenv(_CREDENTIALS_FILE_ENV)

    if raw and creds_path:
        raise RuntimeError(
            "Specify only one of AUTH_USER_CREDENTIALS or AUTH_USER_CREDENTIALS_FILE."
        )

    if creds_path:
        try:
            raw = Path(creds_path).read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - defensive guard for deployment issues
            raise RuntimeError(f"Unable to read credentials file: {creds_path}") from exc

    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "AUTH_USER_CREDENTIALS must be valid JSON mapping usernames to password hashes."
        ) from exc

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "AUTH_USER_CREDENTIALS must be a JSON object mapping usernames to password hashes."
        )

    credentials: dict[str, str] = {}
    for key, value in parsed.items():
        if value is None:
            continue
        value_str = str(value).strip()
        if not value_str:
            raise RuntimeError(
                "AUTH_USER_CREDENTIALS entries must contain non-empty password hashes."
            )
        credentials[str(key)] = value_str

    return credentials


USER_CREDENTIAL_HASHES = _load_user_credentials()


def _verify_password(user_id: str, supplied_password: str) -> bool:
    hashed = USER_CREDENTIAL_HASHES.get(user_id)
    if not hashed:
        hashed = USER_CREDENTIAL_HASHES.get(user_id.lower())
    if not hashed:
        return False
    try:
        return check_password_hash(hashed, supplied_password)
    except (ValueError, TypeError):
        return False

# SQLite-backed refresh token store
_BASE_DIR = Path(__file__).resolve().parent
REFRESH_DB_PATH = os.getenv("REFRESH_DB_PATH", str(_BASE_DIR / "refresh_tokens.db"))


def _with_db(fn):
    """Utility decorator to handle connection lifecycle."""
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(REFRESH_DB_PATH)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS refresh_tokens (user_id TEXT PRIMARY KEY, token TEXT)"
        )
        try:
            result = fn(conn, *args, **kwargs)
            conn.commit()
            return result
        finally:
            conn.close()

    return wrapper


@_with_db
def _store_refresh(conn: sqlite3.Connection, user_id: str, token: str) -> None:
    conn.execute(
        "REPLACE INTO refresh_tokens(user_id, token) VALUES (?, ?)",
        (user_id, token),
    )


@_with_db
def _fetch_refresh(conn: sqlite3.Connection, user_id: str) -> str | None:
    row = conn.execute(
        "SELECT token FROM refresh_tokens WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row[0] if row else None


@_with_db
def _delete_refresh(conn: sqlite3.Connection, user_id: str) -> None:
    conn.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id,))


def _issue_access(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(UTC) + timedelta(seconds=ACCESS_TTL)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def _issue_refresh(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(seconds=MAX_AGE),
        "iat": datetime.now(UTC),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    _store_refresh(user_id, token)
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

    stored = _fetch_refresh(user_id)
    if stored != token:
        _delete_refresh(user_id)
        return None
    return user_id
# ------------------------------------------------------------

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or data.get("email")
    password = data.get("password") or data.get("pw")
    if not user_id or password is None or not _verify_password(user_id, password):
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
        if uid:
            _delete_refresh(uid)

    resp = make_response("", 204)
    # Clear cookie with the same attributes we set
    kwargs = dict(httponly=True, secure=True, samesite=COOKIE_SAMESITE, path=COOKIE_PATH, max_age=0)
    host = (request.host or "").split(":")[0]
    if host.endswith("falowen.app"):
        kwargs["domain"] = ".falowen.app"
    resp.set_cookie(COOKIE_NAME, "", **kwargs)
    return resp
