"""Client-side authentication helpers.

This module hosts logic shared across the Streamlit UI for persisting
session tokens and handling password reset links.  The previous
implementation imported an ``auth_helpers`` module that no longer existed
which meant importing :mod:`src.auth` immediately raised a
``ModuleNotFoundError``.  The helpers are reimplemented here so the UI
can bootstrap cleanly and the behaviour is covered by unit tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4
import logging
import os
from typing import Any, Optional

import bcrypt
import streamlit as st

from .config import get_cookie_manager

try:  # pragma: no cover - optional dependency in some environments
    from google.cloud.firestore_v1 import FieldFilter
except Exception:  # pragma: no cover - fallback when Firestore SDK absent
    FieldFilter = None  # type: ignore

_LOG = logging.getLogger(__name__)
_COOKIE_TOKEN_KEY = "falowen_session_token"
_COOKIE_CODE_KEY = "falowen_student_code"
_COOKIE_EXP_KEY = "falowen_session_expiry"
_COOKIE_DEVICE_KEY = "device_id"
_SESSION_MAX_AGE_ENV = "SESSION_MAX_AGE_DAYS"
_DEFAULT_SESSION_DAYS = 90


def _cookie_ttl_seconds() -> int:
    """Return the cookie lifetime in seconds using the env override if set."""

    raw = os.environ.get(_SESSION_MAX_AGE_ENV, "").strip()
    if not raw:
        return _DEFAULT_SESSION_DAYS * 24 * 60 * 60
    try:
        days = int(raw)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"{_SESSION_MAX_AGE_ENV} must be an integer") from exc
    if days <= 0:
        raise RuntimeError(f"{_SESSION_MAX_AGE_ENV} must be positive (got {days})")
    return days * 24 * 60 * 60


def persist_session_client(
    token: str,
    student_code: str,
    *,
    cookie_manager: Any | None = None,
    st_module: Any = st,
    logger: Any = _LOG,
) -> None:
    """Persist the current session token in cookies and ``st.session_state``.

    ``streamlit_cookies_controller`` is used when available so that the
    browser receives a copy of the token even after Streamlit reruns the
    script.  The helper tolerates missing controllers (for example when
    running tests) by falling back to an in-memory dictionary provided by
    :func:`src.config.get_cookie_manager`.
    """

    if not token:
        logger.warning("persist_session_client called without a token")
        return

    ttl = _cookie_ttl_seconds()
    expires = datetime.now(UTC) + timedelta(seconds=ttl)

    st_module.session_state["session_token"] = token
    if student_code:
        st_module.session_state["student_code"] = student_code
    st_module.session_state["cookie_synced"] = True

    try:
        st_module.query_params["t"] = token
    except Exception:  # pragma: no cover - ``query_params`` missing when testing
        logger.debug("query_params unavailable while persisting session", exc_info=True)

    cm = cookie_manager if cookie_manager is not None else get_cookie_manager()
    if cm is None:
        logger.warning(
            "No cookie manager is configured; browser cookies will not be persisted."
        )
        return
    if not hasattr(cm, "set"):
        logger.warning(
            "Cookie manager %s does not support persistence; skipping cookie writes.",
            type(cm).__name__,
        )
        return

    ready_attr = getattr(cm, "ready", None)
    if ready_attr is not None:
        ready = ready_attr() if callable(ready_attr) else bool(ready_attr)
        if not ready:
            logger.warning("Cookie manager not ready; skipping persistence to avoid errors.")
            return

    cookie_device: str | None = None
    if hasattr(cm, "get"):
        try:
            cookie_device = cm.get(_COOKIE_DEVICE_KEY)  # type: ignore[arg-type]
            if isinstance(cookie_device, tuple):
                cookie_device = cookie_device[0] if cookie_device else None
        except Exception:
            logger.debug("Unable to read device_id from cookie manager", exc_info=True)

    device_id = (cookie_device or st_module.session_state.get("device_id") or "").strip()
    if not device_id:
        device_id = uuid4().hex
    elif device_id != st_module.session_state.get("device_id"):
        logger.debug("Syncing device_id from cookie to session state")
    st_module.session_state["device_id"] = device_id

    try:
        logger.debug(
            "Persisting session cookies with TTL=%s seconds using %s", ttl, type(cm).__name__
        )
        cm.set(_COOKIE_TOKEN_KEY, token)
        cm.set(_COOKIE_CODE_KEY, student_code)
        cm.set(_COOKIE_EXP_KEY, str(int(expires.timestamp())))
        cm.set(
            _COOKIE_DEVICE_KEY,
            device_id,
            max_age=ttl,
            expires=expires.isoformat(),
        )
        save = getattr(cm, "save", None)
        if callable(save):
            save()
    except Exception:
        logger.exception("Failed to persist session cookies")

    # Keep the query string token in sync so hard refreshes stay logged in.
    try:
        st_module.query_params["t"] = token
    except Exception:  # pragma: no cover - ``query_params`` missing when testing
        logger.debug("query_params unavailable while persisting session", exc_info=True)


def _get_db(logger: Any = _LOG) -> Any | None:
    """Return the Firestore client used by ``falowen.sessions`` if possible."""

    try:
        from falowen.sessions import get_db as _get_db  # type: ignore
    except Exception:
        try:
            from falowen.sessions import db as _db  # type: ignore
        except Exception:
            logger.exception("Firestore client unavailable")
            return None

        def _get_db() -> Any:  # type: ignore
            return _db

    try:
        return _get_db()
    except Exception:
        logger.exception("Failed to initialise Firestore client")
        return None


def _lookup_student_ref(db: Any, email: str) -> Any | None:
    """Return a document reference for ``email`` in the ``students`` collection."""

    students = db.collection("students")
    queries = []
    if FieldFilter is not None:
        queries.append(students.where(filter=FieldFilter("email", "==", email)))
        queries.append(students.where(filter=FieldFilter("Email", "==", email)))
    else:  # pragma: no cover - compatibility fallback
        queries.append(students.where("email", "==", email))
        queries.append(students.where("Email", "==", email))

    for query in queries:
        try:
            matches = query.get()
        except Exception:
            continue
        if not matches:
            continue
        doc = matches[0]
        ref = getattr(doc, "reference", None)
        if ref is not None:
            return ref
        doc_id = getattr(doc, "id", None)
        if doc_id:
            return students.document(doc_id)
    return None


def _parse_expires(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).astimezone(UTC)
    except ValueError:
        return None


def reset_password_page(token: str, *, st_module: Any = st, logger: Any = _LOG) -> bool:
    """Render the password reset UI for ``token``.

    The function validates the token stored in ``password_resets``,
    enforces a one hour expiry and updates the student's stored password
    when the form is submitted successfully.
    """

    st_module.title("Reset your password")
    if not token:
        st_module.error("Invalid or expired reset link.")
        return False

    db = _get_db(logger=logger)
    if db is None:
        st_module.error("Password reset service unavailable. Please try again later.")
        return False

    try:
        reset_ref = db.collection("password_resets").document(token)
        reset_doc = reset_ref.get()
    except Exception:
        logger.exception("Failed to load password reset token")
        st_module.error("Password reset link is invalid or has expired.")
        return False

    if not getattr(reset_doc, "exists", False):
        st_module.error("Password reset link is invalid or has expired.")
        return False

    data = reset_doc.to_dict() if hasattr(reset_doc, "to_dict") else None
    email = ((data or {}).get("email") or "").strip().lower()
    expires_at = _parse_expires((data or {}).get("expires_at"))
    if not email or (expires_at and expires_at < datetime.now(UTC)):
        st_module.error("Password reset link is invalid or has expired.")
        try:
            reset_ref.delete()
        except Exception:
            logger.debug("Failed to delete expired reset token", exc_info=True)
        return False

    st_module.info(f"Resetting password for **{email}**")
    with st_module.form("password_reset_form", clear_on_submit=False):
        new_pw = st_module.text_input("New password", type="password")
        confirm_pw = st_module.text_input("Confirm new password", type="password")
        submitted = st_module.form_submit_button("Update password")

    if not submitted:
        return False

    if len(new_pw) < 8:
        st_module.error("Password must be at least 8 characters long.")
        return False
    if new_pw != confirm_pw:
        st_module.error("Passwords do not match.")
        return False

    student_ref = _lookup_student_ref(db, email)
    if student_ref is None:
        st_module.error("No student account matches this reset link.")
        try:
            reset_ref.delete()
        except Exception:
            logger.debug("Failed to delete orphaned reset token", exc_info=True)
        return False

    try:
        hashed = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        student_ref.update({"password": hashed})
        reset_ref.delete()
    except Exception:
        logger.exception("Failed to update password for %s", email)
        st_module.error("We couldn't update your password. Please try again later.")
        return False

    st_module.success("Your password has been updated. You can now log in with the new password.")
    st_module.session_state["need_rerun"] = True
    return True


__all__ = ["persist_session_client", "reset_password_page"]
