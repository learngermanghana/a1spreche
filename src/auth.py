"""Authentication helpers for managing user cookies and sessions."""


from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from streamlit_cookies_manager import EncryptedCookieManager


@dataclass
class SimpleCookieManager:
    """Minimal in-memory cookie store used for tests.

    The production application relies on ``EncryptedCookieManager`` to persist
    cookies in the user's browser.  For unit tests we only need a tiny subset of
    that interface, so this class stores values in memory.
    """

    store: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any, **_: Any) -> None:  # pragma: no cover -
        """Store ``value`` under ``key``."""
        self.store[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:  # pragma: no cover -
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

class BrowserCookieManager(EncryptedCookieManager):
    """Cookie manager that persists values in the browser.

    ``EncryptedCookieManager`` behaves like a mutable mapping but our helper
    functions expect ``set``/``delete`` methods.  This subclass provides those
    small shims so the rest of the code can remain agnostic about the concrete
    implementation.
    """

    def set(self, key: str, value: Any, **_: Any) -> None:  # pragma: no cover -
        self[key] = value

    def delete(self, key: str) -> None:  # pragma: no cover -
        self.pop(key, None)

def set_student_code_cookie(cm: Any, code: str, **kwargs: Any) -> None:
    """Store the student code in a cookie and persist the change."""
    cm.set("student_code", code, **kwargs)
    try:  # pragma: no cover - save rarely fails but we defend against it
        cm.save()
    except Exception:
        pass


def set_session_token_cookie(cm: Any, token: str, **kwargs: Any) -> None:
    """Store the session token in a cookie and persist the change."""
    cm.set("session_token", token, **kwargs)
    try:  # pragma: no cover - save rarely fails but we defend against it
        cm.save()
    except Exception:
        pass

def clear_session(cm: Any) -> None:
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
_session_store: Dict[str, str] = {}


def persist_session_client(token: str, student_code: str) -> None:  # pragma: no cover -
    """Persist a token -> student code mapping for later lookup."""
    _session_store[token] = student_code

def bootstrap_cookies(cm: Optional[Any] = None) -> Any:
    """Create or return a cookie manager for the current session.

    The Streamlit version performs additional initialisation.  The simplified
    implementation just echoes the provided manager which keeps the calling
    code compatible for tests.
    """

    return cm


def restore_session_from_cookie(
    cm: Any, loader: Optional[Callable[[], Any]] = None
) -> Optional[Dict[str, Any]]:
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
        "restored_at": datetime.utcnow(),
    }

def reset_password_page(token: str) -> None:  # pragma: no cover -
    """Placeholder for the password reset flow.

    Parameters
    ----------
    cm:
        Optional cookie manager instance to return.  Tests pass an instance of
        :class:`SimpleCookieManager` to avoid touching the browser.

    Returns
    -------
    Any
        A cookie manager ready for use.  ``None`` is returned when the
        ``EncryptedCookieManager`` is not yet initialised (which happens on the
        first run of a Streamlit script).
    """


__all__ = [
    "SimpleCookieManager",
    "BrowserCookieManager",
    "set_student_code_cookie",
    "set_session_token_cookie",
    "clear_session",
    "persist_session_client",
    "bootstrap_cookies",
    "restore_session_from_cookie",
    "reset_password_page",
]
