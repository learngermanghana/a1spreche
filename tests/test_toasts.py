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


def test_toast_warn(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock())
    monkeypatch.setattr(toasts, "st", mock_st)
    toasts.toast_warn("careful")
    mock_st.toast.assert_called_once_with("careful", icon="⚠️")


def test_toast_info(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock())
    monkeypatch.setattr(toasts, "st", mock_st)
    toasts.toast_info("note")
    mock_st.toast.assert_called_once_with("note", icon="ℹ️")


def test_refresh_with_toast(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock(), session_state={})
    monkeypatch.setattr(toasts, "st", mock_st)
    toasts.refresh_with_toast()
    mock_st.toast.assert_called_once_with("Saved!", icon="✅")
    assert mock_st.session_state["__refresh"] == 1


def test_refresh_with_toast_custom_msg(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock(), session_state={})
    monkeypatch.setattr(toasts, "st", mock_st)
    toasts.refresh_with_toast("Updated!")
    mock_st.toast.assert_called_once_with("Updated!", icon="✅")
    assert mock_st.session_state["__refresh"] == 1


def test_toast_once_suppresses_duplicates(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock(), session_state={})
    monkeypatch.setattr(toasts, "st", mock_st)

    toasts.toast_once("hi", "✅")
    toasts.toast_once("hi", "✅")
    toasts.toast_once("bye", "✅")

    assert mock_st.toast.call_count == 2
    assert mock_st.session_state["__recent_toasts__"] == {"hi", "bye"}
