"""Currency formatting helpers."""
from __future__ import annotations


def format_cedis(amount: float) -> str:
    """Return amount formatted in Ghana cedis.

    A positive ``amount`` is formatted with two decimal places followed by
    ``" cedis"``. Non‑positive values are returned as ``"0"``.
    """
    try:
        value = float(amount)
    except Exception:
        return "0"
    if value > 0:
        return f"{value:,.2f} cedis"
    return "0"
