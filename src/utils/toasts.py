from typing import Set

import streamlit as st

from src.ui.sound import play_ui_sound


_RECENT_TOASTS_KEY = "__recent_toasts__"


def _already_toasted(msg: str) -> bool:
    shown: Set[str] = st.session_state.setdefault(_RECENT_TOASTS_KEY, set())
    if msg in shown:
        return True
    shown.add(msg)
    return False


def toast_once(msg: str, icon: str) -> None:
    """Show a toast message only once per session.

    The function keeps track of messages shown in ``st.session_state`` and
    suppresses duplicates.

    Parameters
    ----------
    msg:
        The message to display.
    icon:
        The icon to display with the toast.
    """
    if not _already_toasted(msg):
        st.toast(msg, icon=icon)
        play_ui_sound(force=True)


def toast_ok(msg: str) -> None:
    """Show a success toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="✅")
    play_ui_sound(force=True)


def toast_err(msg: str) -> None:
    """Show an error toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="❌")
    play_ui_sound(force=True)


def toast_warn(msg: str) -> None:
    """Show a warning toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="⚠️")
    play_ui_sound(force=True)


def toast_info(msg: str) -> None:
    """Show an informational toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="ℹ️")
    play_ui_sound(force=True)


def rerun_without_toast() -> None:
    """Increment ``__refresh`` and flag a rerun without notifying the user."""
    st.session_state["__refresh"] = st.session_state.get("__refresh", 0) + 1
    st.session_state["need_rerun"] = True


def refresh_with_toast(msg: str = "Saved!") -> None:
    """Increment ``__refresh`` and show a saved toast.

    This helper centralises the common pattern of bumping the
    ``__refresh`` counter in ``st.session_state`` to trigger a
    rerender and informing the user that their action was saved.

    Parameters
    ----------
    msg:
        The message to display in the success toast. Defaults to ``"Saved!"``.
    """
    rerun_without_toast()
    toast_ok(msg)
