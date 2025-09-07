from unittest.mock import MagicMock
import types

from src.utils import toasts


def test_toast_ok(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock())
    monkeypatch.setattr(toasts, "st", mock_st)
    toasts.toast_ok("hello")
    mock_st.toast.assert_called_once_with("hello", icon="✅")


def test_toast_err(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock())
    monkeypatch.setattr(toasts, "st", mock_st)
    toasts.toast_err("oops")
    mock_st.toast.assert_called_once_with("oops", icon="❌")
