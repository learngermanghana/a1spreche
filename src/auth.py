"""Authentication helpers for managing user cookies and sessions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


@dataclass
class SimpleCookieManager:
    """Minimal in-memory cookie store used for tests.

    The real application uses the ``streamlit_cookies_manager`` package to
    persist cookies in the browser.  For unit tests we only need a tiny subset
    of the interface, so this class stores cookie values in memory.
    """

    store: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any, **_: Any) -> None:  # pragma: no cover -
        """Store ``value`` under ``key``."""
        self.store[key] = value

    def get(self, key: str, default: Any | None = None) -> Any | None:  # pragma: no cover -
        """Return the value for ``key`` or ``default`` if missing."""
        return self.store.get(key, default)

    def delete(self, key: str) -> None:  # pragma: no cover -
        """Remove ``key`` from the store if present."""
        self.store.pop(key, None)

    def save(self) -> None:  # pragma: no cover -
        """Persist cookies.

        The test implementation keeps cookies in memory so there is nothing to
        do here.
        """
        return None

# A module level instance used by the application
cookie_manager = SimpleCookieManager()


def set_student_code_cookie(cm: SimpleCookieManager, code: str, **kwargs: Any) -> None:
    """Store the student code in a cookie and persist the change."""
    cm.set("student_code", code, **kwargs)
    try:  # pragma: no cover - save rarely fails but we defend against it
        cm.save()
    except Exception:
        pass


def set_session_token_cookie(cm: SimpleCookieManager, token: str, **kwargs: Any) -> None:
    """Store the session token in a cookie and persist the change."""
    cm.set("session_token", token, **kwargs)
    try:  # pragma: no cover - save rarely fails but we defend against it
        cm.save()
    except Exception:
        pass

def clear_session(cm: SimpleCookieManager) -> None:
    """Remove session related cookies.

    Both ``student_code`` and ``session_token`` cookies are deleted from the
    provided cookie manager.  The ``save`` method is invoked to mimic the
    behaviour of the real cookie manager which persists changes to the
    browser.  The function is intentionally tiny so it can be reused by both
    the login and logout flows to avoid token leakage between accounts.
    """

    cm.delete("student_code")
    cm.delete("session_token")
    try:
        cm.save()
    except Exception:  # pragma: no cover - defensive: SimpleCookieManager.save doesn't raise
        pass



# In the real application ``persist_session_client`` would write to a database
# or external cache.  For tests we simply store the mapping in-memory.
_session_store: dict[str, str] = {}


def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover -
    """Persist a token -> student code mapping for later lookup."""
    _session_store[token] = student_code

def bootstrap_cookies(cm: SimpleCookieManager) -> SimpleCookieManager:
    """Return the cookie manager instance.

    The Streamlit version performs additional initialisation.  The simplified
    implementation just echoes the provided manager which keeps the calling
    code compatible for tests.
    """

    return cm


def restore_session_from_cookie(
    cm: SimpleCookieManager, loader: Callable[[], Any] | None = None
) -> Optional[dict[str, Any]]:
    """Attempt to restore a user session from cookies.

    Parameters
    ----------
    cm:
        The cookie manager instance.
    loader:
        Optional callable used to load additional user data.  It is only
        executed when both cookies are present.
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
        "restored_at": datetime.now(timezone.utc),
    }

def reset_password_page(token: str) -> None:  # pragma: no cover -
    """Placeholder for the password reset flow.

    The Streamlit application presents a UI allowing users to change their
    password when they follow a reset link.  For testing purposes this function
    merely exists so that imports succeed and the call site can run without
    side effects.
    """
    return None


__all__ = [
    "cookie_manager",
    "SimpleCookieManager",
    "set_student_code_cookie",
    "set_session_token_cookie",
    "clear_session",
    "persist_session_client",
    "bootstrap_cookies",
    "restore_session_from_cookie",
    "reset_password_page",
]

