"""Helpers for loading optional :mod:`falowen` submodules safely."""

from __future__ import annotations

import importlib
import logging
import sys
from types import ModuleType

LOGGER = logging.getLogger(__name__)


def load_falowen_db() -> ModuleType:
    """Return the ``falowen.db`` module, retrying once if the import half-loads.

    Streamlit's script reloader can sometimes leave ``falowen.db`` in a broken
    state inside :data:`sys.modules`. The next import attempt then bubbles up a
    ``KeyError`` from :mod:`importlib`. To make the application resilient we
    clear the partial entry and try again before giving up.
    """

    module_name = "falowen.db"
    try:
        return importlib.import_module(module_name)
    except KeyError:
        LOGGER.warning("Retrying import for partially-loaded module %s", module_name)
        sys.modules.pop(module_name, None)
        return importlib.import_module(module_name)
