"""Authentication helpers for managing user cookies and sessions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Protocol


# ---- Protocol so both real + test cookie managers are accepted ----------------
class CookieLike(Protocol):
    def set(self, key: str, value: Any, **kwargs: Any) -> None: ...
    def get(self, key: str, default: Any | None = None) -> Any | None: ...
    def delete(self, key: str) -> None: ...
    def save(self) -> None: ...


# ---- Test / fallback in-memory cookie store -----------------------------------
@dataclass
class SimpleCookieManager:
    """Minimal in-memory cookie store used for tests.

    The real application uses the ``streamlit_cookies_manager`` package to
    persist cookies in the browser. For unit tests we only need a tiny subset
    of the interface, so this class stores cookie values in server memory.
    """
    store: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any, **_: Any) -> None:  # pragma: no cover - simple
        self.store[key] = value

    def get(self, key: str, default: Any | None = None) -> Any | None:  # pragma: no cover
        return self.store.get(key, default)

    def delete(self, key: str) -> None:  # pragma: no cover
        self.store.pop(key, None)

    def save(self) -> None:  # pragma: no cover
        return None


# ---- Real cookie manager adapter (per-browser cookies) ------------------------
# We wrap streamlit-cookies-manager to present the same .set/.get/.delete/.save API.
class _CookieAdapter:
    def __init__(self) -> None:
        from streamlit_cookies_manager import CookieManager  # type: ignore
        self.cm = CookieManager()

    def set(self, key: str, value: Any, **kwargs: Any) -> None:
        self.cm[key] = value

    def get(self, key: str, default: Any | None = None) -> Any | None:
        return self.cm.get(key) or default

    def delete(self, key: str) -> None:
        try:
            del self.cm[key]
        except Exception:
            pass

    def save(self) -> None:
        self.cm.save()

    # Expose readiness if caller wants to gate on it.
    def ready(self) -> bool:
        try:
            return bool(self.cm.ready())
        except Exception:
            return True


def _build_cookie_manager() -> CookieLike:
    """Prefer real per-browser cookies; fallback to in-memory for tests/dev."""
    try:
        # If the package is installed, use browser cookies (per-user).
        return _CookieAdapter()
    except Exception:
        # Fallback ONLY for tests: shared in-memory store.
        return SimpleCookieManager()


# NOTE: This module-level instance is safe in production because the adapter
# operates on browser cookies (per user). In tests, it falls back to a local
# in-memory store (single process). For strict isolation in tests, create your
# own SimpleCookieManager per test case instead of importing this one.
cookie_manager: CookieLike = _build_cookie_manager()


# ---- Cookie helpers -----------------------------------------------------------
def set_student_code_cookie(cm: CookieLike, code: str, **kwargs: Any) -> None:
    """Store the student code in a cookie and persist the change."""
    cm.set("student_code", code, **kwargs)
    try:  # pragma: no cover - defensive
        cm.save()
    except Exception:
        pass


def set_session_token_cookie(cm: CookieLike, token: str, **kwargs: Any) -> None:
    """Store the session token in a cookie and persist the change."""
    cm.set("session_token", token, **kwargs)
    try:  # pragma: no cover - defensive
        cm.save()
    except Exception:
        pass


def clear_session(cm: CookieLike) -> None:
    """Remove session-related cookies (student_code, session_token) and persist."""
    cm.delete("student_code")
    cm.delete("session_token")
    try:  # pragma: no cover - defensive
        cm.save()
    except Exception:
        pass


# ---- Session persistence (test double) ----------------------------------------
# In the real application ``persist_session_client`` would write to a database.
# For tests we simply store the mapping in-memory.
_session_store: dict[str, str] = {}


def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover
    """Persist a token -> student code mapping for later lookup (test double)."""
    _session_store[token] = student_code


# ---- Bootstrap / restore helpers ---------------------------------------------
def bootstrap_cookies(cm: CookieLike) -> CookieLike:
    """Return the cookie manager instance and gate on readiness if available.

    The Streamlit implementation may require a `ready()` check. We call it when
    present; in tests it is a no-op.
    """
    try:
        # If underlying manager exposes .ready(), ensure it's ready.
        ready_fn = getattr(cm, "ready", None)
        if callable(ready_fn) and not bool(ready_fn()):
            # Only stop if Streamlit is actually available.
            try:
                import streamlit as st  # type: ignore
                st.stop()
            except Exception:
                pass
    except Exception:
        pass
    return cm


def restore_session_from_cookie(
    cm: CookieLike, loader: Callable[[], Any] | None = None
) -> Optional[dict[str, Any]]:
    """Attempt to restore a user session from cookies.

    Parameters
    ----------
    cm:
        The cookie manager instance.
    loader:
        Optional callable used to load additional user data. It is only executed
        when both cookies are present.
    """
    student_code = cm.get("student_code")
    session_token = cm.get("session_token")
    if not student_code or not session_token:
        return None

    data = loader() if loader else None
    return {
        "student_code": student_code,
        "session_token": session_token,
        "data": data,
        "restored_at": datetime.utcnow(),
    }


def reset_password_page(token: str) -> None:  # pragma: no cover
    """Placeholder for the password reset flow (UI handled elsewhere)."""
    return None


from src.auth import (
    set_student_code_cookie,
    set_session_token_cookie,
    clear_session,
    persist_session_client,
    bootstrap_cookies,
    restore_session_from_cookie,
    reset_password_page,
    cookie_manager as _cookie_manager,  # 👈 add this
)
