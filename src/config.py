"""Application configuration utilities.

This module centralises setup for shared resources such as the
:class:`CookieController`.  ``a1sprechen.py`` previously embedded
this logic directly which made the main script rather unwieldy.  Moving
it here allows tests and other modules to import the initialised cookie
manager without pulling in the whole application.
"""

from __future__ import annotations

import os

import streamlit as st
from streamlit_cookies_controller import CookieController

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
