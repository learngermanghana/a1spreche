"""Application configuration utilities.

This module centralises setup for shared resources such as the
:class:`CookieController`.  ``a1sprechen.py`` previously embedded
this logic directly which made the main script rather unwieldy.  Moving
it here allows tests and other modules to import the initialised cookie
manager without pulling in the whole application.
"""

from __future__ import annotations

import logging
import os

import streamlit as st

try:  # pragma: no cover - import guarded for missing optional dependency
    from streamlit_cookies_controller import CookieController
except ImportError:  # pragma: no cover - executed when dependency missing
    logging.warning(
        "streamlit-cookies-controller not installed; using in-memory cookie"
        " manager. Install with `pip install streamlit-cookies-controller`"
        " for full functionality."
    )

    class CookieController(dict):
        """Minimal in-memory fallback for :class:`CookieController`."""

        ready = True

        def set(self, key: str, value: object, **kwargs: object) -> None:
            self[key] = value

        def delete(self, key: str) -> None:  # pragma: no cover - simple
            self.pop(key, None)

        def save(self) -> None:  # pragma: no cover - no-op for fallback
            return None

from .session_management import bootstrap_cookie_manager

# Default number of sentences per session in Sentence Builder.  This
# constant lives here so that any module may import it without touching
# the main ``a1sprechen`` entrypoint.
SB_SESSION_TARGET = int(os.environ.get("SB_SESSION_TARGET", 5))

# ---------------------------------------------------------------------------
# Cookie manager bootstrap
# ---------------------------------------------------------------------------


def get_cookie_manager() -> CookieController:
    """Return an initialised :class:`CookieController` instance.

    The returned controller is wrapped by ``bootstrap_cookie_manager`` so
    that downstream code receives the same type regardless of environment.
    """

    cookie_manager = st.session_state.get("cookie_manager")
    if cookie_manager is None:
        cookie_manager = bootstrap_cookie_manager(CookieController())
        st.session_state["cookie_manager"] = cookie_manager

    return cookie_manager


__all__ = ["get_cookie_manager", "SB_SESSION_TARGET"]
