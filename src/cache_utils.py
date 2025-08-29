"""Utilities for clearing Streamlit caches in development."""
from __future__ import annotations

import os
import streamlit as st


def clear_cache_if_dev() -> None:
    """Clear Streamlit caches when running in development mode.

    If the ``A1SPRECHEN_DEV`` environment variable is set to ``"1"``,
    both ``st.cache_data`` and ``st.cache_resource`` are cleared. This
    allows developers to refresh cached data quickly while iterating
    locally without impacting production deployments.
    """
    if os.environ.get("A1SPRECHEN_DEV") != "1":
        return

    try:
        st.cache_data.clear()
    except Exception:
        pass

    try:
        st.cache_resource.clear()
    except Exception:
        pass
