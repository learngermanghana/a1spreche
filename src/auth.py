# auth.py
# Authentication helpers for managing user cookies and sessions (Streamlit + iOS/PWA friendly)

from __future__ import annotations

import logging
import os
import threading
from collections.abc import MutableMapping
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import streamlit as st

# Try to use the real encrypted cookie manager; fall back to an in-memory test double if unavailable.
try:  # pragma: no cover - import guard
    from streamlit_cookies_manager import EncryptedCookieManager  # type: ignore
except Exception:  # pragma: no cover - defensive
    EncryptedCookieManager = None  # type: ignore


# ───────────────────────────────────────────────────────────────────────────────
# Cookie defaults (tuned for Safari / iOS / PWA persistence)
# ───────────────────────────────────────────────────────────────────────────────

COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".falowen.app")   # omit/empty for localhost
COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", "2592000")) # 30 days
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")        # use "None" if embedding cross-site

_FALLBACK_COOKIE_PASSWORD = "dev-only-fallback-change-me"

def _cookie_kwargs() -> dict[str, Any]:
    """Standard attributes for auth cookies (persist across refresh/app restarts)."""
    kw: dict[str, Any] = {
        "secure": True,
        "httponly": True,  # EncryptedCookieManager can't make HttpOnly, but harmless to include
        "samesite": COOKIE_SAMESITE,
    }
    if COOKIE_DOMAIN and COOKIE_DOMAIN not in ("localhost", "127.0.0.1"):
        kw["domain"] = COOKIE_DOMAIN
    return kw


def _set_cookie(cm: Any, key: str, value: str, **overrides: Any) -> None:
    """
    Unified cookie setter:
    - uses cm.set(...) if available (real manager)
    - falls back to mapping semantics (tests) and records kwargs for assertions
    """
    kwargs = {**_cookie_kwargs(), **overrides}

    set_fn = getattr(cm, "set", None)
    if callable(set_fn):
        set_fn(key, value, **kwargs)
    else:
        # Fallback for simple/dict-like stores
        cm[key] = value
        if hasattr(cm, "store") and isinstance(cm.store, dict) and key in cm.store:
            cm.store[key]["kwargs"] = kwargs


def save_cookies(cm: Any) -> None:
    """Persist cookies if the manager supports it (EncryptedCookieManager does)."""
    save_fn = getattr(cm, "save", None)
    if callable(save_fn):
        try:
            save_fn()
        except Exception:
            pass


def _expire_cookie(cm: Any, key: str) -> None:
    """Expire cookie in the browser."""
    _set_cookie(cm, key, "", max_age=0, expires=0)


# ───────────────────────────────────────────────────────────────────────────────
# Public cookie helpers
# ───────────────────────────────────────────────────────────────────────────────

def set_student_code_cookie(cm: MutableMapping[str, Any], code: str, **kwargs: Any) -> None:
    _set_cookie(cm, "student_code", code, **kwargs)

def set_session_token_cookie(cm: MutableMapping[str, Any], token: str, **kwargs: Any) -> None:
    _set_cookie(cm, "session_token", token, **kwargs)

def clear_session(cm: MutableMapping[str, Any]) -> None:
    # Expire in browser *and* clear in-memory
    _expire_cookie(cm, "student_code")
    _expire_cookie(cm, "session_token")
    try:
        cm.pop("student_code", None)
        cm.pop("session_token", None)
    except Exception:
        pass


def reset_password_page() -> None:  # pragma: no cover - stub
    """Placeholder for the real reset-password UI."""
    return None


# ───────────────────────────────────────────────────────────────────────────────
# Real cookie manager bootstrap + factory
# ───────────────────────────────────────────────────────────────────────────────

def bootstrap_cookie_manager(cm: Any) -> Any:
    """Return a usable cookie manager.

    If the encrypted manager isn't ready (as is often the case when running
    outside of ``streamlit run``), fall back to ``SimpleCookieManager`` so tests
    and CLI usage still work.
    """
    ready_fn = getattr(cm, "ready", None)
    if callable(ready_fn) and not ready_fn():
        return SimpleCookieManager()
    return cm


def create_cookie_manager() -> Any:
    """Return an EncryptedCookieManager (preferred) or a SimpleCookieManager fallback."""
    if EncryptedCookieManager is None:
        # Fallback for tests/CLI where the plugin isn't installed.
        return SimpleCookieManager()

    cookie_password = (
        st.secrets.get("cookie_password")
        or os.environ.get("COOKIE_PASSWORD")
        or _FALLBACK_COOKIE_PASSWORD
    )

    if cookie_password == _FALLBACK_COOKIE_PASSWORD and os.getenv("DEBUG", "0") == "1":
        logging.warning(
            "Using built-in fallback cookie password (set `cookie_password` or "
            "`COOKIE_PASSWORD` for production)."
        )

    cm = EncryptedCookieManager(password=cookie_password, prefix="falowen")
    return bootstrap_cookie_manager(cm)


# ───────────────────────────────────────────────────────────────────────────────
# SimpleCookieManager: in-memory stand-in for tests/CLI
# ───────────────────────────────────────────────────────────────────────────────

class SimpleCookieManager(MutableMapping[str, Any]):
    """
    In-memory stand-in for browser cookies.

    Values are kept as {"value": ..., "kwargs": ...} so tests can inspect
    attributes written by _set_cookie.
    """
    def __init__(self) -> None:  # pragma: no cover - trivial
        self.store: dict[str, dict[str, Any]] = {}

    # Mapping protocol
    def __getitem__(self, key: str) -> Any:  # pragma: no cover - trivial
        return self.store[key]["value"]

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover - trivial
        self.store[key] = {"value": value, "kwargs": {}}

    def __delitem__(self, key: str) -> None:  # pragma: no cover - trivial
        del self.store[key]

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self.store)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.store)

    # Convenience
    def get(self, key: str, default: Any = None) -> Any:  # noqa: A003
        return self.store.get(key, {}).get("value", default)

    def set(self, key: str, value: Any, **kwargs: Any) -> None:
        self.store[key] = {"value": value, "kwargs": kwargs}

    def pop(self, key: str, default: Any = None) -> Any:  # noqa: A003
        return self.store.pop(key, {}).get("value", default)

    def save(self) -> None:  # keep API parity with real managers
        return None


# ───────────────────────────────────────────────────────────────────────────────
# In-memory session store with TTL (used in tests)
# ───────────────────────────────────────────────────────────────────────────────

class _SessionStore:
    """Simple mapping that expires entries after ``ttl`` seconds."""

    def __init__(self, ttl: int = 60) -> None:
        self.ttl = ttl
        self._data: dict[str, tuple[str, datetime]] = {}

    def set(self, key: str, value: str) -> None:
        self._prune()
        self._data[key] = (value, datetime.now(timezone.utc))

    def get(self, key: str) -> str | None:
        self._prune()
        item = self._data.get(key)
        if not item:
            return None
        value, ts = item
        if (datetime.now(timezone.utc) - ts).total_seconds() > self.ttl:
            self._data.pop(key, None)
            return None
        return value

    def _prune(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [k for k, (_, ts) in self._data.items() if (now - ts).total_seconds() > self.ttl]
        for k in expired:
            self._data.pop(k, None)


# ───────────────────────────────────────────────────────────────────────────────
# Session client mapping (optional convenience)
# ───────────────────────────────────────────────────────────────────────────────

_session_clients: dict[str, str] = {}
_session_lock = threading.Lock()

def persist_session_client(token: str, student_code: str) -> None:
    with _session_lock:
        _session_clients[token] = student_code

def get_session_client(token: str) -> str | None:
    with _session_lock:
        return _session_clients.get(token)

def clear_session_clients() -> None:
    with _session_lock:
        _session_clients.clear()


# ───────────────────────────────────────────────────────────────────────────────
# Session restoration (robust to transient errors; iOS/PWA safe)
# ───────────────────────────────────────────────────────────────────────────────

def restore_session_from_cookie(
    cm: MutableMapping[str, Any],
    loader: Callable[[], Any] | None = None,
    contract_validator: Callable[[str, Any], bool] | None = None,
    contract_checker: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any] | None:
    """
    Attempt to restore a user session from cookies.

    Accepts either `contract_validator` or `contract_checker` for backwards
    compatibility. Only one is needed.
    """
    # Read cookies defensively
    if hasattr(cm, "get"):
        sc = cm.get("student_code")
        token = cm.get("session_token")
    else:
        sc = cm["student_code"] if "student_code" in cm else None
        token = cm["session_token"] if "session_token" in cm else None

    if not sc or not token:
        return None

    # Best-effort UA hash for validation (safe if not present)
    ua_hash = ""
    try:
        ua_hash = st.session_state.get("__ua_hash", "") or ""
    except Exception:
        ua_hash = ""

    # Validate session token with server
    try:
        from falowen.sessions import validate_session_token  # your server-side validator
        res = validate_session_token(token, ua_hash=ua_hash)
    except Exception:
        res = None  # network/server error → do NOT forcibly log out; just fail to restore

    if not res or res.get("student_code") != sc:
        clear_session(cm)
        return None

    # Optional extra data load
    roster = None
    if loader is not None:
        try:
            roster = loader()
        except Exception:
            roster = None

    # Optional contract check (support both names)
    validator = contract_validator or contract_checker
    if validator and roster is not None:
        try:
            if not validator(sc, roster):
                clear_session(cm)
                return None
        except Exception:
            clear_session(cm)
            return None

    return {"student_code": sc, "session_token": token, "data": roster}


__all__ = [
    # factories / bootstrap
    "create_cookie_manager",
    "bootstrap_cookie_manager",
    # cookie helpers
    "set_student_code_cookie",
    "set_session_token_cookie",
    "save_cookies",
    "clear_session",
    # session restore
    "restore_session_from_cookie",
    # optional client map
    "persist_session_client",
    "get_session_client",
    "clear_session_clients",
    # test double
    "SimpleCookieManager",
    "_SessionStore",
    # misc
    "reset_password_page",
]
