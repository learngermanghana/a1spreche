"""Firestore-related helper functions for the a1spreche app.

This module centralises Firestore draft and chat helpers so they can be
re-used outside the monolithic :mod:`a1sprechen` module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

import logging
from firebase_admin import firestore

try:  # Firestore client is optional in test environments
    from falowen.sessions import db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - Firestore may be unavailable
    db = None  # type: ignore


def _extract_level_and_lesson(field_key: str) -> Tuple[str, str]:
    """Extract level and lesson key from a draft field key.

    ``field_key`` values typically look like ``"draft_A2_day3_chX"``.  This
    helper returns a tuple of ``(level, lesson_key)``.  If the key does not
    start with ``"draft_"`` the entire key is treated as the lesson key.
    """

    lesson_key = field_key[6:] if field_key.startswith("draft_") else field_key
    level = (lesson_key.split("_day")[0] or "").upper()
    return level, lesson_key


def _draft_doc_ref(level: str, lesson_key: str, code: str):
    """Return the Firestore document reference for a given draft."""

    if db is None:
        return None
    return (
        db.collection("drafts_v2")
        .document(code)
        .collection("lessons")
        .document(lesson_key)
    )


# ---- DRAFTS (server-side) — now stored separately from submissions ----

def save_draft_to_db(code: str, field_key: str, text: str) -> None:
    """Persist the given ``text`` as a draft for ``code``/``field_key``."""

    if db is None:
        return
    if text is None:
        text = ""
    level, lesson_key = _extract_level_and_lesson(field_key)
    ref = _draft_doc_ref(level, lesson_key, code)
    if ref is None:
        return
    payload = {
        "text": text,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "level": level,
        "lesson_key": lesson_key,
        "student_code": code,
    }

    try:
        ref.set(payload, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save draft for %s/%s: %s", code, field_key, exc)
        return
        
def load_draft_from_db(code: str, field_key: str) -> str:
    """Return the draft text stored for ``code`` and ``field_key``."""

    text, _ = load_draft_meta_from_db(code, field_key)
    return text or ""


def save_chat_draft_to_db(code: str, conv_key: str, text: str) -> None:
    """Persist an unsent chat draft for the given conversation."""

    if db is None:
        return
    ref = db.collection("falowen_chats").document(code)
    try:
        if text:
            ref.set({"drafts": {conv_key: text}}, merge=True)
        else:
            ref.set({"drafts": {conv_key: firestore.DELETE_FIELD}}, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save chat draft for %s/%s: %s", code, conv_key, exc)
        return


def load_chat_draft_from_db(code: str, conv_key: str) -> str:
    """Retrieve any saved chat draft for the conversation."""

    if db is None:
        return ""
    try:
        snap = db.collection("falowen_chats").document(code).get()
        if snap.exists:
            data = snap.to_dict() or {}
            drafts = data.get("drafts", {}) or {}
            return drafts.get(conv_key, "") or ""
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception(
            "Failed to load chat draft for %s/%s: %s", code, conv_key, exc
        )
    return ""


def load_draft_meta_from_db(code: str, field_key: str) -> Tuple[str, Optional[datetime]]:
    """Return ``(text, updated_at)`` for the requested draft."""

    if db is None:
        return "", None
    level, lesson_key = _extract_level_and_lesson(field_key)

    # 1) New user-rooted path
    try:
        ref = _draft_doc_ref(level, lesson_key, code)
        if ref is not None:
            snap = ref.get()
            if snap.exists:
                data = snap.to_dict() or {}
                return data.get("text", ""), data.get("updated_at")
              
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore

        logging.exception(
            "Failed to load draft meta for %s/%s: %s", code, field_key, exc
        )

    # 2) Compatibility: old level-rooted nested path
    try:
        comp = (
            db.collection("drafts_v2")
            .document(level)
            .collection("lessons")
            .document(lesson_key)
            .collection("users")
            .document(code)
            .get()
        )
        if comp.exists:
            data = comp.to_dict() or {}
            return data.get("text", ""), data.get("updated_at")
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception(
            "Failed to load draft meta (compat) for %s/%s: %s", code, field_key, exc
        )

    # 3) Legacy flat doc
    try:
        legacy = db.collection("draft_answers").document(code).get()
        if legacy.exists:
            data = legacy.to_dict() or {}
            return data.get(field_key, ""), data.get(f"{field_key}__updated_at")
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception(
            "Failed to load draft meta (legacy) for %s/%s: %s", code, field_key, exc
        )

    return "", None


# ---- Q&A posts ---------------------------------------------------------------


def _qa_doc_ref(post_id: str):
    """Return the Firestore document reference for a Q&A post."""

    if db is None:
        return None
    return db.collection("qa_posts").document(post_id)


def save_post(code: str, text: str, is_question: bool) -> Optional[str]:
    """Persist a new note or question and return the document ID."""

    if db is None:
        return None
    ref = db.collection("qa_posts").document()
    payload = {
        "text": text or "",
        "student_code": code,
        "created_at": firestore.SERVER_TIMESTAMP,
        "flagged": False,
        "is_question": is_question,
    }
    try:
        ref.set(payload)
        return ref.id
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save post for %s: %s", code, exc)
        return None


def save_ai_answer(post_id: str, ai_text: str, flagged: bool = False) -> None:
    """Attach an AI-generated suggestion to the post."""

    ref = _qa_doc_ref(post_id)
    if ref is None:
        return
    payload = {
        "ai_suggestion": ai_text,
        "ai_created_at": firestore.SERVER_TIMESTAMP,
    }
    if flagged:
        payload["flagged"] = True
    try:
        ref.set(payload, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save AI answer for %s: %s", post_id, exc)


def save_response(post_id: str, text: str, responder_code: str) -> None:
    """Persist a response for a post.

    The response is appended to the ``responses`` array on the post and
    includes the ``responder_code`` and server timestamp.
    """

    ref = _qa_doc_ref(post_id)
    if ref is None:
        return
    payload = {
        "responses": firestore.ArrayUnion([
            {
                "responder_code": responder_code,
                "text": text,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        ])
    }
    try:
        ref.set(payload, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save response for %s: %s", post_id, exc)

