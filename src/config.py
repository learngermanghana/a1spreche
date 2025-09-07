"""Application configuration utilities.

This module centralises setup for shared resources such as the
:class:`EncryptedCookieManager`.  ``a1sprechen.py`` previously embedded
this logic directly which made the main script rather unwieldy.  Moving
it here allows tests and other modules to import the initialised cookie
manager without pulling in the whole application.
"""

from __future__ import annotations

import hashlib
import logging
import os

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from .session_management import bootstrap_cookie_manager

# Streamlit changed the caching API in v1.18.  ``cache_resource`` replaces
# ``experimental_singleton``.  Select whichever decorator is available so that
# repeated calls return the same cookie manager instance without re-inserting
# the component.
_cache_decorator = getattr(st, "cache_resource", st.experimental_singleton)

# Default number of sentences per session in Sentence Builder.  This
# constant lives here so that any module may import it without touching
# the main ``a1sprechen`` entrypoint.
SB_SESSION_TARGET = int(os.environ.get("SB_SESSION_TARGET", 5))

# ---------------------------------------------------------------------------
# Cookie manager bootstrap
# ---------------------------------------------------------------------------

# IMPORTANT: use a long, random phrase (>= 32 chars) in production.  The
# repository contains a short fallback purely so tests can run without
# secrets configured.
_HARDCODED_COOKIE_PASSPHRASE = os.environ.get(
    "FALOWEN_COOKIE_FALLBACK", "Felix029"
)

# Hash the passphrase so the raw value isn't stored directly.
_FALLBACK_COOKIE_PASSWORD = hashlib.sha256(
    _HARDCODED_COOKIE_PASSPHRASE.encode("utf-8")
).hexdigest()


@_cache_decorator
def get_cookie_manager() -> EncryptedCookieManager:
    """Return an initialised :class:`EncryptedCookieManager` instance.

    The password is resolved from ``st.secrets`` or environment variables
    with a deterministic fallback suitable for development and tests.
    The returned manager is wrapped by ``bootstrap_cookie_manager`` so
    that downstream code receives the same type regardless of environment.
    """

    cookie_password = (
        st.secrets.get("cookie_password", None)
        or os.environ.get("COOKIE_PASSWORD")
        or _FALLBACK_COOKIE_PASSWORD
    )

    if cookie_password == _FALLBACK_COOKIE_PASSWORD and os.getenv("DEBUG", "0") == "1":
        logging.warning(
            "Using built-in fallback cookie password (set `cookie_password` or `COOKIE_PASSWORD` for production)."
        )

    return bootstrap_cookie_manager(
        EncryptedCookieManager(password=cookie_password, prefix="falowen")
    )


__all__ = ["get_cookie_manager", "SB_SESSION_TARGET"]
