from unittest.mock import MagicMock

from src import data_loading


def test_force_refresh_clears_cache(monkeypatch):
    loader = MagicMock(return_value={"data": "fresh"})
    loader.clear = MagicMock()
    monkeypatch.setattr(data_loading, "_load_student_data_cached", loader)

    result = data_loading.load_student_data(force_refresh=True)

    assert result == {"data": "fresh"}
    loader.clear.assert_called_once_with()
    loader.assert_called_once_with()
