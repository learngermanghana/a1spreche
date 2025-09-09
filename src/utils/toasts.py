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


def toast_warn(msg: str) -> None:
    """Show a warning toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="⚠️")


def toast_info(msg: str) -> None:
    """Show an informational toast message.

    Parameters
    ----------
    msg:
        The message to display.
    """
    st.toast(msg, icon="ℹ️")


def refresh_with_toast() -> None:
    """Increment ``__refresh`` and show a saved toast.

    This helper centralises the common pattern of bumping the
    ``__refresh`` counter in ``st.session_state`` to trigger a
    rerender and informing the user that their action was saved.
    """
    st.session_state["__refresh"] = st.session_state.get("__refresh", 0) + 1
    toast_ok("Saved!")
