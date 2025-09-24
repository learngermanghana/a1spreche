from unittest.mock import MagicMock
import types

from src.utils import toasts


def _patch_toast_and_sound(monkeypatch):
    mock_toast = MagicMock()
    mock_sound = MagicMock()
    mock_st = types.SimpleNamespace(toast=mock_toast, session_state={})
    monkeypatch.setattr(toasts, "st", mock_st)
    monkeypatch.setattr(toasts, "play_ui_sound", mock_sound)
    return mock_st, mock_sound


def test_toast_ok(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)
    toasts.toast_ok("hello")
    mock_st.toast.assert_called_once_with("hello", icon="✅")
    mock_sound.assert_called_once_with(force=True)


def test_toast_err(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)
    toasts.toast_err("oops")
    mock_st.toast.assert_called_once_with("oops", icon="❌")
    mock_sound.assert_called_once_with(force=True)


def test_toast_warn(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)
    toasts.toast_warn("careful")
    mock_st.toast.assert_called_once_with("careful", icon="⚠️")
    mock_sound.assert_called_once_with(force=True)


def test_toast_info(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)
    toasts.toast_info("note")
    mock_st.toast.assert_called_once_with("note", icon="ℹ️")
    mock_sound.assert_called_once_with(force=True)


def test_rerun_without_toast(monkeypatch):
    mock_st = types.SimpleNamespace(toast=MagicMock(), session_state={})
    monkeypatch.setattr(toasts, "st", mock_st)
    monkeypatch.setattr(toasts, "play_ui_sound", MagicMock())
    toasts.rerun_without_toast()
    mock_st.toast.assert_not_called()
    assert mock_st.session_state["__refresh"] == 1
    assert mock_st.session_state["need_rerun"] is True


def test_refresh_with_toast(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)
    toasts.refresh_with_toast()
    mock_st.toast.assert_called_once_with("Saved!", icon="✅")
    mock_sound.assert_called_once_with(force=True)
    assert mock_st.session_state["__refresh"] == 1
    assert mock_st.session_state["need_rerun"] is True


def test_refresh_with_toast_custom_msg(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)
    toasts.refresh_with_toast("Updated!")
    mock_st.toast.assert_called_once_with("Updated!", icon="✅")
    mock_sound.assert_called_once_with(force=True)
    assert mock_st.session_state["__refresh"] == 1
    assert mock_st.session_state["need_rerun"] is True


def test_toast_once_suppresses_duplicates(monkeypatch):
    mock_st, mock_sound = _patch_toast_and_sound(monkeypatch)

    toasts.toast_once("hi", "✅")
    toasts.toast_once("hi", "✅")
    toasts.toast_once("bye", "✅")

    assert mock_st.toast.call_count == 2
    assert mock_sound.call_count == 2
    assert mock_st.session_state["__recent_toasts__"] == {"hi", "bye"}
