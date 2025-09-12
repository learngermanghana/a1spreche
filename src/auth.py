"""Authentication helpers for managing user cookies and sessions."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Callable, Optional
from collections.abc import MutableMapping

# --------------------------------------------------------------------
# Minimal cookie manager for tests (in-memory)
# --------------------------------------------------------------------
@dataclass
class SimpleCookieManager(MutableMapping[str, Any]):
    """Minimal in-memory cookie store used for tests."""
    store: dict[str, dict[str, Any]] = field(default_factory=dict)

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

    def pop(self, key: str, default: Any | None = None) -> Any | None:  # pragma: no cover
        item = self.store.pop(key, None)
        if item is None:
            return default
        return item.get("value")

    def set(self, key: str, value: Any, **kwargs: Any) -> None:  # pragma: no cover
        self.store[key] = {"value": value, "kwargs": kwargs}

    def get(self, key: str, default: Any | None = None) -> Any | None:  # pragma: no cover
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
    "path": "/",
    "domain": ".falowen.app",  # make sure you always serve from https://www.falowen.app
}

def _cm_save(cm: Any) -> None:
    saver = getattr(cm, "save", None)
    if callable(saver):
        try:
            saver()
        except Exception:
            logging.exception("Cookie save failed")

def _cm_set(cm: MutableMapping[str, Any] | Any, key: str, value: Any, **kwargs: Any) -> None:
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
        if isinstance(store, dict) and key in store:
            store[key]["kwargs"] = cookie_args

# Public cookie ops used by the app
def set_student_code_cookie(cm: MutableMapping[str, Any] | Any, code: str, **kwargs: Any) -> None:
    _cm_set(cm, "student_code", code, **kwargs)

def set_session_token_cookie(cm: MutableMapping[str, Any] | Any, token: str, **kwargs: Any) -> None:
    _cm_set(cm, "session_token", token, **kwargs)

def clear_session(cm: MutableMapping[str, Any] | Any) -> None:
    try:
        # Try CookieManager.delete if available
        deleter = getattr(cm, "delete", None)
        if callable(deleter):
            deleter("student_code")
            deleter("session_token")
            _cm_save(cm)
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
    _cm_save(cm)

# --------------------------------------------------------------------
# Session token registry (in-memory)
# --------------------------------------------------------------------
class _SessionStore:
    """In-memory mapping of session token to student code."""

    def __init__(self, ttl: int = 3600) -> None:  # pragma: no cover
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

def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover
    _session_store.set(token, student_code)

def get_session_client(token: str) -> str | None:  # pragma: no cover
    return _session_store.get(token)

def clear_session_clients() -> None:  # pragma: no cover
    _session_store.clear()

def bootstrap_cookies(cm: SimpleCookieManager) -> SimpleCookieManager:
    return cm

# --------------------------------------------------------------------
# Cookie-based session restoration
# --------------------------------------------------------------------
def restore_session_from_cookie(
    cm: SimpleCookieManager | Any,
    loader: Callable[[], Any] | None = None,
    contract_validator: Callable[[str, Any], bool] | None = None,
) -> Optional[dict[str, Any]]:
    """Attempt to restore a user session from cookies."""
    student_code = None
    session_token = None

    # Prefer CookieManager.get; fall back to mapping
    getter = getattr(cm, "get", None)
    if callable(getter):
        student_code = getter("student_code")
        session_token = getter("session_token")
    else:
        try:
            student_code = cm.get("student_code")  # type: ignore[attr-defined]
            session_token = cm.get("session_token")  # type: ignore[attr-defined]
        except Exception:
            try:
                student_code = cm["student_code"]  # type: ignore[index]
                session_token = cm["session_token"]  # type: ignore[index]
            except Exception:
                pass

    if not student_code or not session_token:
        return None

    # Best-effort user-agent hash
    ua_hash = ""
    try:  # pragma: no cover - environment dependent
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

    # Validate the token
    from falowen.sessions import validate_session_token

    session_data = validate_session_token(session_token, ua_hash=ua_hash)
    if not session_data or session_data.get("student_code") != student_code:
        clear_session(cm)
        return None

    # Test safety: if validator returns a *different* student_code, do NOT restore
    if isinstance(session_data, dict):
        sc = session_data.get("student_code")
        if sc and sc != student_code:
            clear_session(cm)
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

def recover_session_from_qp_token() -> None:  # pragma: no cover - network
    """Recreate cookies from ``?t=`` query parameter if present."""
    try:
        import streamlit as st
    except Exception:  # pragma: no cover
        return

    tok = st.query_params.get("t")
    if isinstance(tok, list):
        tok = tok[0] if tok else None
    if not tok:
        return

    from falowen.sessions import validate_session_token

    session_data = validate_session_token(tok, ua_hash=st.session_state.get("__ua_hash", ""))
    student_code = session_data.get("student_code") if isinstance(session_data, dict) else None

    cm = st.session_state.get("cookie_manager")
    if cm is not None and student_code:
        persist_session_client(tok, student_code)
        set_student_code_cookie(
            cm, student_code, expires=datetime.now(timezone.utc) + timedelta(days=180)
        )
        set_session_token_cookie(
            cm, tok, expires=datetime.now(timezone.utc) + timedelta(days=30)
        )

    if "t" in st.query_params:
        del st.query_params["t"]
    st.rerun()

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
    "restore_session_from_cookie",
    "recover_session_from_qp_token",
    "reset_password_page",
]
