# auth.py
from datetime import UTC, datetime, timedelta
from flask import Blueprint, request, jsonify, make_response
import json
import os
import jwt
import uuid
import sqlite3
from pathlib import Path
from typing import Iterable, Sequence


from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

COOKIE_NAME = "session"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")  # use "None" if cross-site; requires HTTPS
COOKIE_PATH = "/"
_DEFAULT_MAX_AGE_DAYS = 90
_MAX_AGE_ENV = "SESSION_MAX_AGE_DAYS"


def _load_cookie_max_age() -> int:
    """Return the cookie lifetime (in seconds) from env or default."""

    raw_days = os.getenv(_MAX_AGE_ENV, "").strip()
    if not raw_days:
        return _DEFAULT_MAX_AGE_DAYS * 24 * 60 * 60

    try:
        days = int(raw_days)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"{_MAX_AGE_ENV} must be an integer number of days") from exc

    if days <= 0:
        raise RuntimeError(f"{_MAX_AGE_ENV} must be a positive integer (got {days})")

    return days * 24 * 60 * 60


MAX_AGE = _load_cookie_max_age()

def _set_cookie(resp, token: str, *, device_id: str | None = None):
    """
    Sets the session cookie. If running under falowen.app, use domain=.falowen.app.
    Otherwise (e.g., testing on <app>.herokuapp.com), omit domain so the cookie is set.
    """
    expires = datetime.now(UTC) + timedelta(seconds=MAX_AGE)
    kwargs = dict(
        max_age=MAX_AGE,
        expires=expires,
        httponly=True,
        secure=True,                 # requires HTTPS (Cloudflare/Heroku provide this)
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
    )
    host = (request.host or "").split(":")[0]
    if host.endswith("falowen.app"):
        kwargs["domain"] = ".falowen.app"  # share across www/api if needed

    resp.set_cookie(COOKIE_NAME, token, **kwargs)

    if device_id:
        device_kwargs = dict(kwargs)
        device_kwargs["httponly"] = False
        resp.set_cookie("device_id", device_id, **device_kwargs)
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


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create or migrate the refresh token store to the current schema."""

    info = conn.execute("PRAGMA table_info(refresh_tokens)").fetchall()
    columns = [row[1] for row in info]
    pk_map = {row[1]: row[5] for row in info}

    if not info:
        conn.execute(
            """
            CREATE TABLE refresh_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_id TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    elif pk_map.get("user_id") == 1 and "token" in columns and pk_map.get("token") != 1:
        existing: Sequence[tuple[str, str]] = conn.execute(
            "SELECT user_id, token FROM refresh_tokens"
        ).fetchall()
        conn.execute("ALTER TABLE refresh_tokens RENAME TO refresh_tokens_legacy")
        conn.execute(
            """
            CREATE TABLE refresh_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                device_id TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        if existing:
            conn.executemany(
                "INSERT OR IGNORE INTO refresh_tokens(token, user_id) VALUES (?, ?)",
                [(row[1], row[0]) for row in existing if row[1]],
            )
        conn.execute("DROP TABLE refresh_tokens_legacy")
    else:
        if "device_id" not in columns:
            conn.execute("ALTER TABLE refresh_tokens ADD COLUMN device_id TEXT")
        if "user_agent" not in columns:
            conn.execute("ALTER TABLE refresh_tokens ADD COLUMN user_agent TEXT")
        if "created_at" not in columns:
            conn.execute(
                "ALTER TABLE refresh_tokens ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)"
    )


def _with_db(fn):
    """Utility decorator to handle connection lifecycle."""

    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(REFRESH_DB_PATH)
        _ensure_schema(conn)
        try:
            result = fn(conn, *args, **kwargs)
            conn.commit()
            return result
        finally:
            conn.close()

    return wrapper


def _resolve_device_id() -> tuple[str | None, bool]:
    """Return a best-effort stable identifier for the current device."""

    headers: Iterable[str] = (
        request.headers.get("X-Device-Id", ""),
        request.headers.get("X-Device-ID", ""),
    )
    for candidate in headers:
        candidate = (candidate or "").strip()
        if candidate:
            return candidate[:128], False

    cookie_device = (request.cookies.get("device_id") or "").strip()
    if cookie_device:
        return cookie_device[:128], False

    return uuid.uuid4().hex, True


@_with_db
def _store_refresh(
    conn: sqlite3.Connection,
    user_id: str,
    token: str,
    device_id: str | None,
    user_agent: str | None,
) -> None:
    if device_id:
        conn.execute(
            "DELETE FROM refresh_tokens WHERE user_id = ? AND device_id = ?",
            (user_id, device_id),
        )
    conn.execute(
        """
        INSERT INTO refresh_tokens(token, user_id, device_id, user_agent, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(token) DO UPDATE SET
            user_id = excluded.user_id,
            device_id = excluded.device_id,
            user_agent = excluded.user_agent,
            created_at = CURRENT_TIMESTAMP
        """,
        (token, user_id, device_id, user_agent),
    )


@_with_db
def _fetch_refresh(
    conn: sqlite3.Connection, token: str
) -> tuple[str | None, str | None]:
    row = conn.execute(
        "SELECT user_id, device_id FROM refresh_tokens WHERE token = ?", (token,)
    ).fetchone()
    if not row:
        return None, None
    return row[0], row[1]


@_with_db
def _delete_refresh(
    conn: sqlite3.Connection,
    *,
    token: str | None = None,
    user_id: str | None = None,
    device_id: str | None = None,
) -> None:
    if token:
        conn.execute("DELETE FROM refresh_tokens WHERE token = ?", (token,))
        return
    if user_id and device_id:
        conn.execute(
            "DELETE FROM refresh_tokens WHERE user_id = ? AND device_id = ?",
            (user_id, device_id),
        )
        return
    if user_id:
        conn.execute("DELETE FROM refresh_tokens WHERE user_id = ?", (user_id,))


def _issue_access(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(UTC) + timedelta(seconds=ACCESS_TTL)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def _issue_refresh(user_id: str) -> tuple[str, str | None]:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(seconds=MAX_AGE),
        "iat": datetime.now(UTC),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
    device_id, _ = _resolve_device_id()
    user_agent = request.headers.get("User-Agent")
    _store_refresh(user_id, token, device_id, user_agent)
    return token, device_id


def _get_user_from_refresh(token: str) -> str | None:
    """Validate refresh token and return user_id if valid, else None."""
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        if data.get("type") != "refresh":
            raise jwt.InvalidTokenError("not refresh")
        user_id = data["sub"]
    except jwt.PyJWTError:
        return None

    stored_user, _ = _fetch_refresh(token)
    if stored_user != user_id:
        _delete_refresh(token=token)
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
    refresh, device_id = _issue_refresh(user_id)

    resp = make_response(jsonify(
        access_token=access,
        refresh_token=refresh,
        expires_in=3600
    ), 200)
    _set_cookie(resp, refresh, device_id=device_id)   # persist on web via HttpOnly cookie
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
    new_refresh, device_id = _issue_refresh(user_id)

    resp = make_response(jsonify(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=3600
    ), 200)
    _set_cookie(resp, new_refresh, device_id=device_id)   # extend cookie expiry for web
    return resp

@auth_bp.post("/logout")
def logout():
    rt = request.cookies.get(COOKIE_NAME)
    if rt:
        uid = _get_user_from_refresh(rt)
        if uid:
            _delete_refresh(token=rt)

    resp = make_response("", 204)
    # Clear cookie with the same attributes we set
    kwargs = dict(
        httponly=True,
        secure=True,
        samesite=COOKIE_SAMESITE,
        path=COOKIE_PATH,
        max_age=0,
        expires=0,
    )
    host = (request.host or "").split(":")[0]
    if host.endswith("falowen.app"):
        kwargs["domain"] = ".falowen.app"
    resp.set_cookie(COOKIE_NAME, "", **kwargs)
    return resp
