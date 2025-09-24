"""Helpers for persisting Topic Coach transcripts to Firestore.

This module contains small utilities that mirror the lightweight
Topic Coach chat experience implemented directly inside
``a1sprechen.py``.  They are deliberately side-effect free so that tests
can exercise the Firestore integration logic without importing the
Streamlit app entrypoint.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import logging

TOPIC_COACH_CHAT_KEY = "topic_coach"
TOPIC_COACH_META_FIELD = "topic_coach_meta"
_FOCUS_TIPS_FIELD = "focus_tips"


def _coerce_messages(value: Any) -> List[Dict[str, Any]]:
    """Return ``value`` as a list of message dictionaries."""

    if isinstance(value, list):
        # Defensive copy so callers can mutate without affecting the
        # cached Firestore data returned by :meth:`~google.cloud.firestore.DocumentSnapshot.to_dict`.
        return [dict(item) if isinstance(item, dict) else item for item in value]
    return []


def get_topic_coach_doc(db: Any, student_code: str):
    """Return the Firestore document reference for Topic Coach chats."""

    if db is None or not student_code:
        return None
    try:
        return db.collection("falowen_chats").document(student_code)
    except Exception as exc:  # pragma: no cover - safety net for unexpected SDK failures
        logging.warning("Failed to resolve Topic Coach doc for %s: %s", student_code, exc)
        return None


def load_topic_coach_state(db: Any, student_code: str) -> Tuple[Any, List[Dict[str, Any]], Dict[str, Any]]:
    """Return ``(doc_ref, messages, meta)`` for the student's Topic Coach chat."""

    doc_ref = get_topic_coach_doc(db, student_code)
    if doc_ref is None:
        return None, [], {}

    try:
        snapshot = doc_ref.get()
    except Exception as exc:  # pragma: no cover - safety net for unexpected SDK failures
        logging.warning("Failed to load Topic Coach transcript for %s: %s", student_code, exc)
        return doc_ref, [], {}

    data: Dict[str, Any] = {}
    if getattr(snapshot, "exists", False):
        try:
            data = snapshot.to_dict() or {}
        except Exception as exc:  # pragma: no cover - defensive guard for bad snapshots
            logging.warning("Topic Coach snapshot conversion failed for %s: %s", student_code, exc)
            data = {}

    chats = data.get("chats") or {}
    raw_messages = chats.get(TOPIC_COACH_CHAT_KEY) if isinstance(chats, dict) else []
    messages = _coerce_messages(raw_messages)

    raw_meta = data.get(TOPIC_COACH_META_FIELD)
    meta = raw_meta if isinstance(raw_meta, dict) else {}

    return doc_ref, messages, meta


def _coerce_focus_tips(value: Any) -> List[str]:
    """Return a list of cleaned focus-tip strings."""

    tips: List[str] = []
    if not value:
        return tips
    if isinstance(value, dict):
        iterable: Iterable[Any] = value.values()
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        iterable = value
    else:
        return tips

    for item in iterable:
        text = str(item).strip()
        if text:
            tips.append(text)
    return tips


def _normalise_meta(qcount: Any, finalised: Any, focus_tips: Any = None) -> Dict[str, Any]:
    """Return a Firestore-friendly metadata payload."""

    try:
        qcount_value = int(qcount or 0)
    except Exception:
        qcount_value = 0
    payload: Dict[str, Any] = {
        "qcount": max(0, qcount_value),
        "finalized": bool(finalised),
    }
    tips = _coerce_focus_tips(focus_tips)
    if tips:
        payload[_FOCUS_TIPS_FIELD] = tips[:3]
    elif isinstance(focus_tips, Iterable) and not isinstance(focus_tips, (str, bytes)):
        # Explicitly clear tips when caller provides an empty iterable.
        payload[_FOCUS_TIPS_FIELD] = []
    return payload


def persist_topic_coach_state(
    doc_ref: Any,
    *,
    messages: Iterable[Dict[str, Any]],
    qcount: Any,
    finalized: Any,
    focus_tips: Any = None,
) -> bool:
    """Persist the latest Topic Coach state to Firestore.

    Returns ``True`` when the write is attempted successfully and ``False``
    when no document reference is available or the SDK raises an error.
    """

    if doc_ref is None:
        return False

    payload = {
        "chats": {TOPIC_COACH_CHAT_KEY: list(messages or [])},
        TOPIC_COACH_META_FIELD: _normalise_meta(qcount, finalized, focus_tips),
    }

    try:
        doc_ref.set(payload, merge=True)
        return True
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        doc_id = getattr(doc_ref, "id", "<unknown>")
        logging.warning("Failed to persist Topic Coach transcript for %s: %s", doc_id, exc)
        return False
