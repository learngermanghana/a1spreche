import logging
import os
import threading
from collections.abc import MutableMapping
from typing import Any, Callable

import streamlit as st

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
        "samesite": COOKIE_SAMESITE,  # "Lax" is fine for first-party; use "None" for iframes
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

    # Callers may persist using ``cm.save()`` if supported; we avoid
    # auto-saving here so multiple cookie operations can be batched before a
    # single save call.

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



def reset_password_page():  # pragma: no cover - stub for compatibility
    """Placeholder for the real reset-password UI."""
    return None


# --- Simple cookie manager for tests/CLI -----------------------------------


class SimpleCookieManager(MutableMapping[str, Any]):
    """In-memory stand-in for browser cookies.

    The object behaves like a mapping whose values are stored in ``store`` as
    ``{"value": ..., "kwargs": ...}`` so tests can introspect cookie
    attributes written by :func:`_set_cookie`.
    """

    def __init__(self) -> None:  # pragma: no cover - trivial
        self.store: dict[str, dict[str, Any]] = {}

    # --- Mapping protocol -------------------------------------------------
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

    # --- Convenience helpers --------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:  # noqa: A003 - mirror dict API
        return self.store.get(key, {}).get("value", default)

    def set(self, key: str, value: Any, **kwargs: Any) -> None:
        self.store[key] = {"value": value, "kwargs": kwargs}

    def pop(self, key: str, default: Any = None) -> Any:  # noqa: A003 - mirror dict API
        return self.store.pop(key, {}).get("value", default)


def create_cookie_manager() -> SimpleCookieManager:
    """Return a new ``SimpleCookieManager`` instance.

    The real application uses Streamlit's cookie manager. For tests and other
    environments where it may not be available, a simple in-memory
    implementation suffices.
    """

    return SimpleCookieManager()


# --- Session client persistence --------------------------------------------

_session_clients: dict[str, str] = {}
_session_lock = threading.Lock()


def persist_session_client(token: str, student_code: str) -> None:
    """Remember which student code is associated with a session token."""

    with _session_lock:
        _session_clients[token] = student_code


def get_session_client(token: str) -> str | None:
    """Return the student code for ``token`` if known."""

    with _session_lock:
        return _session_clients.get(token)


def clear_session_clients() -> None:
    """Remove all persisted session mappings."""

    with _session_lock:
        _session_clients.clear()


# --- Session restoration ---------------------------------------------------


def restore_session_from_cookie(
    cm: MutableMapping[str, Any],
    loader: Callable[[], Any] | None = None,
    contract_checker: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any] | None:
    """Restore a session based on cookies.

    Parameters
    ----------
    cm:
        Cookie manager or mapping with ``student_code`` and ``session_token``.
    loader:
        Optional callable returning roster/roster-like data.
    contract_checker:
        Optional callable taking ``(student_code, roster)`` and returning
        ``True`` if the session is still valid.
    """

    sc = getattr(cm, "get", lambda k, d=None: cm[k] if k in cm else d)(
        "student_code"
    )
    token = getattr(cm, "get", lambda k, d=None: cm[k] if k in cm else d)(
        "session_token"
    )

    if not sc or not token:
        return None

    ua_hash = st.session_state.get("__ua_hash", "")

    try:
        from falowen.sessions import validate_session_token

        res = validate_session_token(token, ua_hash)
    except Exception:
        res = None

    if not res or res.get("student_code") != sc:
        clear_session(cm)
        return None

    roster = None
    if loader is not None:
        try:
            roster = loader()
        except Exception:
            roster = None

    if contract_checker and roster is not None:
        try:
            if not contract_checker(sc, roster):
                clear_session(cm)
                return None
        except Exception:
            clear_session(cm)
            return None

    return {"student_code": sc, "session_token": token, "data": roster}


