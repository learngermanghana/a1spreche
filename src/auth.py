import logging
import os
from datetime import datetime, timedelta, timezone
from collections.abc import MutableMapping
from typing import Any, Iterator


# --- SimpleCookieManager ----------------------------------------------------

class SimpleCookieManager(MutableMapping[str, str]):
    """A minimal in-memory cookie store.

    The real application uses ``streamlit_cookies_manager`` which exposes a
    mapping-like interface plus ``set`` and ``save`` methods.  The test suite
    only requires a lightweight stand in that behaves similarly without any
    external dependencies.  Values are stored along with any keyword arguments
    provided so tests can inspect cookie metadata recorded by :func:`_set_cookie`.
    """

    def __init__(self) -> None:  # pragma: no cover - trivial
        self.store: dict[str, dict[str, Any]] = {}

    # -- MutableMapping protocol -----------------------------------------
    def __getitem__(self, key: str) -> str:
        return self.store[key]["value"]

    def __setitem__(self, key: str, value: str) -> None:
        # ``kwargs`` will be populated by ``set`` or ``_set_cookie`` later.
        self.store[key] = {"value": value, "kwargs": {}}

    def __delitem__(self, key: str) -> None:
        del self.store[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.store)

    def __len__(self) -> int:
        return len(self.store)

    # -- Convenience methods ---------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:  # pragma: no cover - simple
        return self.store.get(key, {}).get("value", default)

    def set(self, key: str, value: str, **kwargs: Any) -> None:
        """Mimic ``EncryptedCookieManager.set``.

        ``_set_cookie`` will use this when available to attach metadata.
        """

        self.store[key] = {"value": value, "kwargs": dict(kwargs)}

    def save(self) -> None:  # pragma: no cover - no-op for tests
        """Placeholder for API compatibility.

        Real cookie managers persist cookies to the browser.  The simple
        manager stores everything in memory so ``save`` is a no-op but tests
        may override it to track calls.
        """

        return None



import streamlit as st

# --- Cookie defaults --------------------------------------------------------

COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", ".falowen.app")  # leave empty on localhost
COOKIE_MAX_AGE = int(os.getenv("COOKIE_MAX_AGE", "2592000"))  # 30 days
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")         # or "None" if you embed cross-site

def _cookie_kwargs() -> dict:
    """Standard cookie attributes for auth cookies."""
    kw = {
        "path": "/",
        "secure": True,
        "httponly": True,
        "samesite": COOKIE_SAMESITE,  # "Lax" is fine for first-party; use "None" for iframes
        "max_age": COOKIE_MAX_AGE,
        # some libs accept either 'expires' (datetime) or 'max_age'
        "expires": datetime.now(timezone.utc) + timedelta(seconds=COOKIE_MAX_AGE),
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

    # Persist if supported (streamlit_cookies_manager uses .save()).
    # Our SimpleCookieManager intentionally requires an explicit save, so we
    # only call ``save`` automatically for other implementations.
    save_fn = getattr(cm, "save", None)
    if callable(save_fn) and not isinstance(cm, SimpleCookieManager):
        try:
            save_fn()
        except Exception:
            pass

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


def create_cookie_manager() -> SimpleCookieManager:
    """Return a new :class:`SimpleCookieManager` instance.

    This mirrors the behaviour of ``get_cookie_manager`` in the real
    application but keeps the implementation lightweight for tests.
    Each invocation returns an isolated cookie store.
    """

    return SimpleCookieManager()


