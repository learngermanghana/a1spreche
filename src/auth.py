"""Authentication helpers for managing user cookies and sessions."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Callable, Optional
import importlib


@dataclass
class SimpleCookieManager:
    """Minimal in-memory cookie store used for tests.

    The real application uses the ``streamlit_cookies_manager`` package to
    persist cookies in the browser.  For unit tests we only need a tiny subset
    of the interface, so this class stores cookie values in memory.
    """

    store: dict[str, dict[str, Any]] = field(default_factory=dict)

    def set(self, key: str, value: Any, **kwargs: Any) -> None:  # pragma: no cover -
        """Store ``value`` and any options under ``key``."""
        self.store[key] = {"value": value, "kwargs": kwargs}

    def get(self, key: str, default: Any | None = None) -> Any | None:  # pragma: no cover -
        """Return the stored value for ``key`` or ``default`` if missing."""
        item = self.store.get(key)
        if item is None:
            return default
        return item.get("value")

    def delete(self, key: str) -> None:  # pragma: no cover -
        """Remove ``key`` from the store if present."""
        self.store.pop(key, None)

    def save(self) -> None:  # pragma: no cover -
        """Persist cookies.

        The test implementation keeps cookies in memory so there is nothing to
        do here.
        """
        return None


# Factory helper so each session receives its own cookie manager instance.
def create_cookie_manager() -> SimpleCookieManager:
    """Return a fresh ``SimpleCookieManager``."""
    return SimpleCookieManager()


def set_student_code_cookie(cm: SimpleCookieManager, code: str, **kwargs: Any) -> None:
    """Store the student code in a cookie and persist the change."""
    cookie_args = {"httponly": True, "secure": True, "samesite": "Strict"}
    cookie_args.update(kwargs)
    cm.set("student_code", code, **cookie_args)
    try:  # pragma: no cover - save rarely fails but we defend against it
        cm.save()
    except Exception:
        logging.exception("Failed to save student code cookie")


def set_session_token_cookie(cm: SimpleCookieManager, token: str, **kwargs: Any) -> None:
    """Store the session token in a cookie and persist the change."""
    cookie_args = {"httponly": True, "secure": True, "samesite": "Strict"}
    cookie_args.update(kwargs)
    cm.set("session_token", token, **cookie_args)
    try:  # pragma: no cover - save rarely fails but we defend against it
        cm.save()
    except Exception:
        pass


def clear_session(cm: SimpleCookieManager) -> None:
    """Remove session related cookies."""
    cm.delete("student_code")
    cm.delete("session_token")
    try:
        cm.save()
    except Exception as exc:  # pragma: no cover - defensive
        logging.warning("Failed to persist cleared cookies: %s", exc)


# In the real application ``persist_session_client`` would write to a database.
class _SessionStore:
    """In-memory mapping of session token to student code."""

    def __init__(self, ttl: int = 3600) -> None:  # pragma: no cover - trivial
        self._store: dict[str, tuple[str, datetime]] = {}
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

    def get(self, token: str) -> str | None:
        with self._lock:
            self._prune_locked()
            data = self._store.get(token)
            return data[0] if data else None

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


_session_store = _SessionStore()


def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover -
    _session_store.set(token, student_code)


def get_session_client(token: str) -> str | None:  # pragma: no cover - convenience
    return _session_store.get(token)


def clear_session_clients() -> None:  # pragma: no cover - test helper
    _session_store.clear()


def bootstrap_cookies(cm: SimpleCookieManager) -> SimpleCookieManager:
    return cm


def restore_session_from_cookie(
    cm: SimpleCookieManager,
    loader: Callable[[], Any] | None = None,
    contract_validator: Callable[[str, Any], bool] | None = None,
) -> Optional[dict[str, Any]]:
    """Attempt to restore a user session from cookies."""
    student_code = cm.get("student_code")
    session_token = cm.get("session_token")
    if not student_code or not session_token:
        return None

    ua_hash = ""
    try:
        import streamlit as st  # type: ignore
        ua_hash = st.session_state.get("__ua_hash", "") or ""
        if not ua_hash:
            try:
                from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
                import hashlib
                ctx = get_script_run_ctx()
                if ctx and getattr(ctx, "session_info", None):
                    client = getattr(ctx.session_info, "client", None)
                    ua = getattr(client, "user_agent", "") if client else ""
                    if ua:
                        ua_hash = hashlib.sha256(ua.encode("utf-8")).hexdigest()
            except Exception:
                ua_hash = ""
    except Exception:
        ua_hash = ""

    from falowen.sessions import validate_session_token
    session_data = validate_session_token(session_token, ua_hash=ua_hash)
    if not session_data:
        return None

    data = loader() if loader else None
    if contract_validator and not contract_validator(student_code, data):
        clear_session(cm)
        return None
    return {
        "student_code": student_code,
        "session_token": session_token,
        "data": data,
        "restored_at": datetime.now(timezone.utc),
    }


def reset_password_page(token: str) -> None:  # pragma: no cover -
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
    "restore_session_from_cookie",
    "reset_password_page",
]
