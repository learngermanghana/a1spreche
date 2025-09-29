"""Utilities for handling forum post timers and countdown indicators."""
from __future__ import annotations

from datetime import datetime as _dt, timezone as _timezone, UTC
from typing import Any, Dict, Optional
import math

try:  # pragma: no cover - optional dependency
    from dateutil import parser as _dateparse  # type: ignore
except Exception:  # pragma: no cover - gracefully handle missing dependency
    _dateparse = None  # type: ignore


def to_datetime_any(value: Any) -> Optional[_dt]:
    """Best-effort conversion of Firestore/JSON datetime payloads."""
    if value is None:
        return None

    dt_val: Optional[_dt]

    if isinstance(value, _dt):
        dt_val = value
    else:
        dt_val = None
        try:
            if hasattr(value, "to_datetime"):
                dt_val = value.to_datetime()
        except Exception:
            dt_val = None

        if dt_val is None:
            try:
                if hasattr(value, "seconds"):
                    dt_val = _dt.fromtimestamp(int(value.seconds), _timezone.utc)
            except Exception:
                dt_val = None

        if dt_val is None and _dateparse is not None:
            try:
                dt_val = _dateparse.parse(str(value))
            except Exception:
                dt_val = None

        if dt_val is None:
            for fmt in (
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
            ):
                try:
                    dt_val = _dt.strptime(str(value), fmt)
                    break
                except Exception:
                    continue

    if dt_val is not None and dt_val.tzinfo is None:
        dt_val = dt_val.replace(tzinfo=_timezone.utc)

    return dt_val


def build_forum_timer_indicator(
    expires_at: Any, *, now: Optional[_dt] = None
) -> Dict[str, Optional[Any]]:
    """Return metadata describing the countdown label for a forum timer."""
    dt_val = to_datetime_any(expires_at)
    if dt_val is None:
        return {"label": "", "status": "none", "minutes": None, "expires_at": None}

    ref_now = now or _dt.now(UTC)
    remaining_seconds = (dt_val - ref_now).total_seconds()
    if remaining_seconds <= 0:
        return {
            "label": "Forum closed",
            "status": "closed",
            "minutes": 0,
            "expires_at": dt_val,
        }

    minutes_left = max(1, math.ceil(remaining_seconds / 60.0))
    label = f"⏳ {minutes_left} minute{'s' if minutes_left != 1 else ''} left"
    return {
        "label": label,
        "status": "open",
        "minutes": minutes_left,
        "expires_at": dt_val,
    }


def build_forum_reply_indicator_text(timer_info: Optional[Dict[str, Any]]) -> str:
    """Return the countdown/closed label to display near the reply composer."""
    if not timer_info:
        return ""

    status = timer_info.get("status")
    label = timer_info.get("label") or ""
    if status in {"open", "closed"} and label:
        return str(label)
    return ""


# Backwards-compatible private aliases for modules expecting these helpers
_to_datetime_any = to_datetime_any

__all__ = [
    "to_datetime_any",
    "_to_datetime_any",
    "build_forum_timer_indicator",
    "build_forum_reply_indicator_text",
]
