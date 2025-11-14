"""Authentication helpers for managing user cookies and sessions."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple, Union
from collections.abc import MutableMapping
from types import SimpleNamespace

try:  # pragma: no cover - streamlit isn't always available during tests
    import streamlit as st
except Exception:  # pragma: no cover
    st = SimpleNamespace(session_state={}, query_params={})

# --------------------------------------------------------------------
# Minimal cookie manager for tests (in-memory)
# --------------------------------------------------------------------
@dataclass
class SimpleCookieManager(MutableMapping[str, Any]):
    """Minimal in-memory cookie store used for tests."""
    store: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:  # pragma: no cover
        item = self.store[key]
        return item.get("value")

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover
        self.set(key, value)

    def __delitem__(self, key: str) -> None:  # pragma: no cover
        self.delete(key)

    def __iter__(self):  # pragma: no cover
        return iter(self.store)

    def __len__(self) -> int:  # pragma: no cover
        return len(self.store)

    def pop(self, key: str, default: Optional[Any] = None) -> Optional[Any]:  # pragma: no cover
        item = self.store.pop(key, None)
        if item is None:
            return default
        return item.get("value")

    def set(self, key: str, value: Any, **kwargs: Any) -> None:  # pragma: no cover
        self.store[key] = {"value": value, "kwargs": kwargs}

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:  # pragma: no cover
        item = self.store.get(key)
        if item is None:
            return default
        return item.get("value")

    def delete(self, key: str) -> None:  # pragma: no cover
        self.store.pop(key, None)

    def clear(self) -> None:  # pragma: no cover
        self.store.clear()

    def save(self) -> None:  # pragma: no cover
        return None


def create_cookie_manager() -> SimpleCookieManager:
    """Return a fresh ``SimpleCookieManager`` (used by tests)."""
    return SimpleCookieManager()

# --------------------------------------------------------------------
# Cookie write helpers (robust across managers)
# --------------------------------------------------------------------
_DEFAULT_COOKIE_KW = {
    "httponly": True,
    "secure": True,
    "samesite": "Lax",
    "domain": ".falowen.app",  # make sure you always serve from https://www.falowen.app
}

def _cm_save(cm: Any) -> None:
    saver = getattr(cm, "save", None)
    if callable(saver):
        try:
            saver()
        except Exception:
            logging.exception("Cookie save failed")

def _cm_set(
    cm: Union[MutableMapping[str, Any], object], key: str, value: Any, **kwargs: Any
) -> None:
    """
    Try cookie_manager.set(key, value, **kwargs). Fall back to mapping semantics
    (for SimpleCookieManager/tests). Tracks kwargs in SimpleCookieManager.store for assertions.
    """
    cookie_args = dict(_DEFAULT_COOKIE_KW)
    cookie_args.update(kwargs or {})

    setter = getattr(cm, "set", None)
    if callable(setter):
        # Try full arg set first
        try:
            setter(key, value, **cookie_args)
        except TypeError:
            # Some managers don't accept path/domain/httponly; try a reduced set
            reduced = {k: cookie_args[k] for k in ("secure", "samesite") if k in cookie_args}
            if "expires" in cookie_args:
                reduced["expires"] = cookie_args["expires"]
            try:
                setter(key, value, **reduced)
            except Exception:
                # Final fallback: set value only
                setter(key, value)
        return

    # Mapping fallback (tests)
    try:
        cm[key] = value  # type: ignore[index]
    except Exception:
        # Last resort: attribute set (unlikely)
        setattr(cm, key, value)
    if hasattr(cm, "store"):
        store = getattr(cm, "store", {})
        if isinstance(store, dict) and key in store:
            store[key]["kwargs"] = cookie_args

# Public cookie ops used by the app
def set_student_code_cookie(
    cm: Union[MutableMapping[str, Any], object], code: str, **kwargs: Any
) -> None:
    _cm_set(cm, "student_code", code, **kwargs)

def set_session_token_cookie(
    cm: Union[MutableMapping[str, Any], object], token: str, **kwargs: Any
) -> None:
    _cm_set(cm, "session_token", token, **kwargs)

def clear_session(cm: Union[MutableMapping[str, Any], object]) -> None:
    try:
        # Try CookieManager.delete if available
        deleter = getattr(cm, "delete", None)
        if callable(deleter):
            deleter("student_code")
            deleter("session_token")
            return
    except Exception:
        pass
    # Mapping fallback
    try:
        cm.pop("student_code", None)  # type: ignore[attr-defined]
        cm.pop("session_token", None)  # type: ignore[attr-defined]
    except Exception:
        # Very defensive
        try:
            del cm["student_code"]  # type: ignore[index]
        except Exception:
            pass
        try:
            del cm["session_token"]  # type: ignore[index]
        except Exception:
            pass

# --------------------------------------------------------------------
# Session token registry (in-memory)
# --------------------------------------------------------------------
class _SessionStore:
    """In-memory mapping of session token to student code."""

    def __init__(self, ttl: int = 3600) -> None:  # pragma: no cover
        self._store: Dict[str, Tuple[str, datetime]] = {}
        self._lock = Lock()
        self._ttl = ttl

    def _prune_locked(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self._ttl)
        expired = [tok for tok, (_, ts) in self._store.items() if ts < cutoff]
        for tok in expired:
            self._store.pop(tok, None)

    def prune(self) -> None:
        with self._lock:
            self._prune_locked()

    def set(self, token: str, student_code: str) -> None:
        with self._lock:
            self._store[token] = (student_code, datetime.now(timezone.utc))
            self._prune_locked()

    def get(self, token: str) -> Optional[str]:
        with self._lock:
            self._prune_locked()
            data = self._store.get(token)
            return data[0] if data else None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

# --------------------------------------------------------------------
# Global session store (shared across all tabs/sessions)
# --------------------------------------------------------------------
_GLOBAL_SESSION_STORE: Optional[_SessionStore] = None

def get_session_store(st_module=st) -> _SessionStore:
    """
    Return a process-wide ``_SessionStore`` shared across all tabs/sessions.

    The st_module argument is kept for backwards-compatibility but is not used
    anymore, so tests that call get_session_store(st_module=...) still work.
    """
    global _GLOBAL_SESSION_STORE
    if _GLOBAL_SESSION_STORE is None:
        _GLOBAL_SESSION_STORE = _SessionStore()
    return _GLOBAL_SESSION_STORE


def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover
    get_session_store().set(token, student_code)


def get_session_client(token: str) -> Optional[str]:  # pragma: no cover
    return get_session_store().get(token)


def clear_session_clients() -> None:  # pragma: no cover
    """Clear all stored session mappings."""
    global _GLOBAL_SESSION_STORE
    if _GLOBAL_SESSION_STORE is not None:
        _GLOBAL_SESSION_STORE.clear()

def bootstrap_cookies(cm: SimpleCookieManager) -> SimpleCookieManager:
    return cm

# --------------------------------------------------------------------
# Cookie-based session restoration
# --------------------------------------------------------------------

def reset_password_page(token: str) -> None:  # pragma: no cover
    """Placeholder for the password reset flow."""
    return None

__all__ = [
    "SimpleCookieManager",
    "create_cookie_manager",
    "set_student_code_cookie",
    "set_session_token_cookie",
    "clear_session",
    "persist_session_client",
    "get_session_client",
    "clear_session_clients",
    "bootstrap_cookies",
    "reset_password_page",
]
