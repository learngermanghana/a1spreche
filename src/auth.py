"""Authentication helpers for managing user cookies and sessions (updated)."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Optional, Tuple, Union, Dict
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
def _default_cookie_kwargs(**overrides: Any) -> Dict[str, Any]:
    """
    Build cookie kwargs with safe defaults.
    - No hard-coded domain. If you want one, set env COOKIE_DOMAIN.
    - Lax samesite; secure+httponly by default.
    """
    domain = os.getenv("COOKIE_DOMAIN")  # e.g. ".yourdomain.com"; omit for current host
    base = {
        "httponly": True,
        "secure": True,
        "samesite": "Lax",
        # "domain": domain  # set only if provided
    }
    if domain:
        base["domain"] = domain
    base.update(overrides or {})
    return base


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
    cookie_args = _default_cookie_kwargs(**kwargs)

    setter = getattr(cm, "set", None)
    if callable(setter):
        # Try full arg set first
        try:
            setter(key, value, **cookie_args)
        except TypeError:
            # Some managers don’t accept all kwargs; retry with a reduced set.
            reduced = {k: cookie_args[k] for k in ("secure", "samesite") if k in cookie_args}
            if "expires" in cookie_args:
                reduced["expires"] = cookie_args["expires"]
            if "domain" in cookie_args:
                # Some managers accept domain; keep it if possible
                reduced["domain"] = cookie_args["domain"]
            try:
                setter(key, value, **reduced)
            except Exception:
                setter(key, value)
        _cm_save(cm)
        return

    # Mapping fallback (tests)
    try:
        cm[key] = value  # type: ignore[index]
    except Exception:
        # Last resort: attribute set (unlikely)
        setattr(cm, key, value)
    if hasattr(cm, "store"):
        store = getattr(cm, "store", {})
        if isinstance(store, dict):
            store[key] = {"value": value, "kwargs": cookie_args}
    _cm_save(cm)


def _cm_delete(cm: Union[MutableMapping[str, Any], object], key: str) -> None:
    deleter = getattr(cm, "delete", None)
    if callable(deleter):
        try:
            deleter(key)
            _cm_save(cm)
            return
        except Exception:
            pass
    try:
        if isinstance(cm, MutableMapping):
            cm.pop(key, None)  # type: ignore[attr-defined]
        else:
            delattr(cm, key)  # type: ignore[attr-defined]
    except Exception:
        pass
    _cm_save(cm)


def _cm_get(cm: Union[MutableMapping[str, Any], object], key: str, default: Any = None) -> Any:
    getter = getattr(cm, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            # Some managers use get(key) only
            try:
                return getter(key)
            except Exception:
                pass
    # Mapping fallback
    try:
        if isinstance(cm, MutableMapping):
            return cm.get(key, default)  # type: ignore[attr-defined]
    except Exception:
        pass
    # Attribute fallback
    return getattr(cm, key, default)


# Public cookie ops used by the app
def set_student_code_cookie(
    cm: Union[MutableMapping[str, Any], object], code: str, *, days: int = 7, **kwargs: Any
) -> None:
    expires = kwargs.pop("expires", datetime.now(timezone.utc) + timedelta(days=days))
    _cm_set(cm, "student_code", code, expires=expires, **kwargs)


def set_session_token_cookie(
    cm: Union[MutableMapping[str, Any], object], token: str, *, days: int = 7, **kwargs: Any
) -> None:
    expires = kwargs.pop("expires", datetime.now(timezone.utc) + timedelta(days=days))
    _cm_set(cm, "session_token", token, expires=expires, **kwargs)


def clear_session(cm: Union[MutableMapping[str, Any], object]) -> None:
    _cm_delete(cm, "student_code")
    _cm_delete(cm, "session_token")


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


def get_session_store(st_module=st) -> _SessionStore:
    """Return the per-session ``_SessionStore`` from ``st.session_state``."""
    ss = st_module.session_state
    store = ss.get("_session_store")
    if store is None:
        store = _SessionStore()
        ss["_session_store"] = store
    return store


def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover
    get_session_store().set(token, student_code)


def get_session_client(token: str) -> Optional[str]:  # pragma: no cover
    return get_session_store().get(token)


def clear_session_clients() -> None:  # pragma: no cover
    ss = getattr(st, "session_state", None)
    if ss is None:
        return
    store = ss.pop("_session_store", None)
    if store is not None:
        store.clear()


def bootstrap_cookies(cm: SimpleCookieManager) -> SimpleCookieManager:
    """Hook to adjust a cookie manager instance at startup if needed."""
    return cm


# --------------------------------------------------------------------
# Cookie-based session restoration (helpers you can call on page load)
# --------------------------------------------------------------------
def read_student_code(cm: Union[MutableMapping[str, Any], object]) -> Optional[str]:
    return _cm_get(cm, "student_code")


def read_session_token(cm: Union[MutableMapping[str, Any], object]) -> Optional[str]:
    return _cm_get(cm, "session_token")


def restore_session_from_cookies(cm: Union[MutableMapping[str, Any], object]) -> Optional[str]:
    """
    If a session token cookie exists, surface the student code from our in-memory
    store (if previously persisted) and return it. This is a best-effort helper.
    """
    tok = read_session_token(cm)
    if not tok:
        return None
    return get_session_client(tok)


def reset_password_page(token: str) -> None:  # pragma: no cover
    """Placeholder for the password reset flow."""
    return None


__all__ = [
    # cookie manager + creation
    "SimpleCookieManager",
    "create_cookie_manager",
    # cookie ops
    "set_student_code_cookie",
    "set_session_token_cookie",
    "clear_session",
    "read_student_code",
    "read_session_token",
    "restore_session_from_cookies",
    # session store
    "persist_session_client",
    "get_session_client",
    "clear_session_clients",
    "bootstrap_cookies",
    "reset_password_page",
]
