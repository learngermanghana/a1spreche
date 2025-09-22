import importlib
from unittest.mock import MagicMock

import pytest


MODULES = [
    "src.firestore_helpers",
    "src.schreiben",
    "src.ui.auth",
]


class _SentinelFieldFilter:
    """Simple stand-in that stores the arguments it was initialised with."""

    def __init__(self, *args):
        self.args = args


@pytest.mark.parametrize("module_name", MODULES)
def test_firestore_where_prefers_filter(monkeypatch, module_name):
    module = importlib.import_module(module_name)
    query = MagicMock()
    chained = MagicMock(name="filtered_query")
    query.where.return_value = chained

    monkeypatch.setattr(module, "FieldFilter", _SentinelFieldFilter, raising=False)

    result = module._firestore_where(query, "field", "==", "value")

    query.where.assert_called_once()
    kwargs = query.where.call_args.kwargs
    assert "filter" in kwargs
    sentinel = kwargs["filter"]
    assert isinstance(sentinel, _SentinelFieldFilter)
    assert sentinel.args == ("field", "==", "value")
    assert result is chained


@pytest.mark.parametrize("module_name", MODULES)
def test_firestore_where_fallback(monkeypatch, module_name):
    module = importlib.import_module(module_name)
    query = MagicMock()
    chained = MagicMock(name="filtered_query")
    query.where.return_value = chained

    monkeypatch.setattr(module, "FieldFilter", None, raising=False)

    result = module._firestore_where(query, "field", "==", "value")

    query.where.assert_called_once_with("field", "==", "value")
    assert result is chained
