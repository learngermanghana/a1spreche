import types
from unittest.mock import MagicMock

from src import cache_utils


def test_clear_cache_if_dev(monkeypatch):
    cd_clear = MagicMock()
    cr_clear = MagicMock()
    st_mock = types.SimpleNamespace(
        cache_data=types.SimpleNamespace(clear=cd_clear),
        cache_resource=types.SimpleNamespace(clear=cr_clear),
    )
    monkeypatch.setattr(cache_utils, "st", st_mock)
    monkeypatch.setenv("A1SPRECHEN_DEV", "1")

    cache_utils.clear_cache_if_dev()

    cd_clear.assert_called_once()
    cr_clear.assert_called_once()


def test_clear_cache_if_dev_disabled(monkeypatch):
    cd_clear = MagicMock()
    cr_clear = MagicMock()
    st_mock = types.SimpleNamespace(
        cache_data=types.SimpleNamespace(clear=cd_clear),
        cache_resource=types.SimpleNamespace(clear=cr_clear),
    )
    monkeypatch.setattr(cache_utils, "st", st_mock)
    monkeypatch.delenv("A1SPRECHEN_DEV", raising=False)

    cache_utils.clear_cache_if_dev()

    cd_clear.assert_not_called()
    cr_clear.assert_not_called()
