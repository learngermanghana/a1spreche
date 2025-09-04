import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from collections.abc import MutableMapping
from typing import Any, Callable

import pandas as pd
import streamlit as st

_session_clients: dict[str, str] = {}
_session_lock = threading.Lock()

import streamlit as st

# --- Cookie defaults --------------------------------------------------------

COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".falowen.app")  # leave empty on localhost
COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", "2592000"))  # 30 days
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")         # or "None" if you embed cross-site

def _cookie_kwargs() -> dict:
    """Standard cookie attributes for auth cookies."""
    kw = {
        "secure": True,
        "httponly": True,
        "samesite": COOKIE_SAMESITE,
    }
    # Only set Domain when we're actually on a real domain (not localhost)
    if COOKIE_DOMAIN and COOKIE_DOMAIN not in ("localhost", "127.0.0.1"):
        kw["domain"] = COOKIE_DOMAIN
    return kw

def _set_cookie(cm, key: str, value: str, **overrides):
    """
    Unified cookie setter:
    - uses cm.set(...) if available (real manager)
    - falls back to mapping semantics (tests) and records kwargs for assertions
    """
    kwargs = {**_cookie_kwargs(), **overrides}

    # Real cookie managers usually expose .set()
    set_fn = getattr(cm, "set", None)
    if callable(set_fn):
        set_fn(key, value, **kwargs)
    else:
        # Fallback for the SimpleCookieManager/dict-like stores
        cm[key] = value
        if hasattr(cm, "store") and isinstance(cm.store, dict) and key in cm.store:
            cm.store[key]["kwargs"] = kwargs

    # Saving is left to the caller

def _expire_cookie(cm, key: str):
    """Tell the browser to delete the cookie."""
    _set_cookie(cm, key, "", max_age=0, expires=0)

# --- Public helpers ---------------------------------------------------------

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

class SimpleCookieManager(MutableMapping[str, Any]):
    """In-memory cookie manager used for tests."""

    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def __getitem__(self, key: str) -> Any:  # pragma: no cover - simple mapping
        return self.store[key]["value"]

    def __setitem__(self, key: str, value: Any) -> None:
        self.store[key] = {"value": value}

    def __delitem__(self, key: str) -> None:  # pragma: no cover - simple mapping
        self.store.pop(key, None)

    def __iter__(self):  # pragma: no cover - simple mapping
        return iter(self.store)

    def __len__(self) -> int:  # pragma: no cover - simple mapping
        return len(self.store)

    def get(self, key: str, default: Any = None) -> Any:
        return self.store.get(key, {}).get("value", default)

    def pop(self, key: str, default: Any = None) -> Any:  # pragma: no cover - simple mapping
        return self.store.pop(key, {"value": default})["value"]

    def ready(self) -> bool:  # pragma: no cover - trivial
        return True

    def save(self) -> None:  # pragma: no cover - trivial
        pass


def create_cookie_manager() -> MutableMapping[str, Any]:
    """Return a cookie manager instance."""
    try:  # pragma: no cover - optional dependency
        from streamlit_cookies_manager import EncryptedCookieManager

        return EncryptedCookieManager()
    except Exception:  # pragma: no cover - fallback for tests
        return SimpleCookieManager()


class _SessionStore:
    """TTL cache for session token mappings."""

    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self._data: dict[str, tuple[str, datetime]] = {}

    def set(self, token: str, student_code: str) -> None:
        self._data[token] = (student_code, datetime.now(timezone.utc))
        self._prune()

    def get(self, token: str) -> str | None:
        self._prune()
        item = self._data.get(token)
        return item[0] if item else None

    def _prune(self) -> None:
        if not self.ttl:
            return
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.ttl)
        expired = [k for k, (_, ts) in self._data.items() if ts < cutoff]
        for k in expired:
            del self._data[k]


def persist_session_client(token: str, student_code: str) -> None:
    """Store token to student mapping."""
    with _session_lock:
        _session_clients[token] = student_code


def get_session_client(token: str) -> str | None:
    """Retrieve stored student code."""
    with _session_lock:
        return _session_clients.get(token)


def clear_session_clients() -> None:
    """Remove all persisted mappings."""
    with _session_lock:
        _session_clients.clear()


def restore_session_from_cookie(
    cm: MutableMapping[str, Any],
    loader: Callable[[], pd.DataFrame] | None = None,
    contract_checker: Callable[[str, pd.DataFrame], bool] | None = None,
) -> dict[str, Any] | None:
    """Validate cookies and return session details if valid."""
    sc = cm.get("student_code")
    token = cm.get("session_token")
    if not sc or not token:
        return None

    from falowen.sessions import validate_session_token

    ua_hash = st.session_state.get("__ua_hash", "")
    info = validate_session_token(token, ua_hash)
    if not info or info.get("student_code") != sc:
        clear_session(cm)
        return None

    data = loader() if loader is not None else None
    if contract_checker is not None and data is not None:
        try:
            if not contract_checker(sc, data):
                clear_session(cm)
                return None
        except Exception:  # pragma: no cover - defensive
            clear_session(cm)
            return None

    return {"student_code": sc, "session_token": token, "data": data}


def reset_password_page() -> None:  # pragma: no cover - placeholder
    """Stub for password reset page."""
    pass
