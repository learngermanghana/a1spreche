"""Firestore session helpers for Falowen."""

import base64
import os
import time
from typing import Optional

import firebase_admin
import requests
import streamlit as st
from firebase_admin import credentials, firestore

_db_client: Optional[firestore.Client] = None
db: Optional[firestore.Client] = None  # backwards-compat for tests


def get_db() -> firestore.Client:
    """Return a cached Firestore client."""

    global _db_client, db
    if db is not None:
        return db
    if _db_client is not None:
        db = _db_client
        return _db_client
    try:  # pragma: no cover - runtime side effects
        if not firebase_admin._apps:  # guard against re-init
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        _db_client = firestore.client()
        db = _db_client
        return _db_client
    except Exception as e:  # pragma: no cover - streamlit UI feedback
        st.error(f"Firebase init failed: {e}")
        raise RuntimeError("Firebase initialization failed") from e

SESSIONS_COL = "sessions"
SESSION_TTL_MIN = 60 * 24 * 14  # 14 days
SESSION_ROTATE_AFTER_MIN = 60 * 24 * 7  # 7 days


def _rand_token(nbytes: int = 48) -> str:
    return base64.urlsafe_b64encode(os.urandom(nbytes)).rstrip(b"=").decode("ascii")


def create_session_token(student_code: str, name: str, ua_hash: str = "") -> str:
    db = get_db()
    now = time.time()
    token = _rand_token()
    db.collection(SESSIONS_COL).document(token).set(
        {
            "student_code": (student_code or "").strip().lower(),
            "name": name or "",
            "issued_at": now,
            "expires_at": now + (SESSION_TTL_MIN * 60),
            "ua_hash": ua_hash or "",
        }
    )
    return token


def validate_session_token(token: str, ua_hash: str = "") -> Optional[dict]:
    if not token:
        return None
    db = get_db()
    try:
        snap = db.collection(SESSIONS_COL).document(token).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        if float(data.get("expires_at", 0)) < time.time():
            return None
        if data.get("ua_hash") and ua_hash and data["ua_hash"] != ua_hash:
            return None
        return data
    except Exception:
        return None


def refresh_or_rotate_session_token(token: str) -> str:
    """Extend session TTL and rotate token periodically without crashing the app."""
    db = get_db()
    try:
        ref = db.collection(SESSIONS_COL).document(token)
        snap = ref.get()
        if not snap.exists:
            return token

        data = snap.to_dict() or {}
        now = time.time()

        # Extend TTL
        ref.update({"expires_at": now + (SESSION_TTL_MIN * 60)})

        # Rotate if older than threshold
        if now - float(data.get("issued_at", now)) > (SESSION_ROTATE_AFTER_MIN * 60):
            new_token = _rand_token()
            db.collection(SESSIONS_COL).document(new_token).set(
                {
                    **data,
                    "issued_at": now,
                    "expires_at": now + (SESSION_TTL_MIN * 60),
                }
            )
            try:
                ref.delete()
            except Exception:
                pass
            return new_token

    except Exception as e:  # pragma: no cover - streamlit UI feedback
        st.warning(f"Session rotation warning: {e}")
    return token


def destroy_session_token(token: str) -> None:
    db = get_db()
    try:
        db.collection(SESSIONS_COL).document(token).delete()
    except Exception:
        pass


def api_get(url, headers=None, params=None, **kwargs):
    headers = headers or {}
    params = params or {}
    tok = st.session_state.get("session_token", "")
    if tok:
        headers.setdefault("X-Session-Token", tok)
        params.setdefault("session_token", tok)
    return requests.get(url, headers=headers, params=params, **kwargs)


def api_post(url, headers=None, params=None, **kwargs):
    headers = headers or {}
    params = params or {}
    tok = st.session_state.get("session_token", "")
    if tok:
        headers.setdefault("X-Session-Token", tok)
        params.setdefault("session_token", tok)
    return requests.post(url, headers=headers, params=params, **kwargs)
