import streamlit as st


def toast_ok(msg: str) -> None:
    """Show a success toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="✅")


def toast_err(msg: str) -> None:
    """Show an error toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="❌")
