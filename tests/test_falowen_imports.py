import importlib
import sys

from src.utils.falowen_imports import load_falowen_db


def test_load_falowen_db_retries_after_keyerror(monkeypatch):
    """The helper should clear broken cache entries and retry once."""

    real_import_module = importlib.import_module
    sentinel = object()
    attempts = {"count": 0}

    def fake_import_module(name, package=None):
        if name == "falowen.db":
            attempts["count"] += 1
            if attempts["count"] == 1:
                sys.modules[name] = sentinel
                raise KeyError(name)
            assert sys.modules.get(name) is not sentinel
        return real_import_module(name, package=package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    module = load_falowen_db()

    assert module.__name__ == "falowen.db"
    assert attempts["count"] == 2
