"""Persistence helpers for the Assignment Helper chat experience.

This module mirrors :mod:`src.topic_coach_persistence` but keeps the
implementation scoped to the Assignment Helper tab so that tests and other
callers can exercise the Firestore integration without importing the
Streamlit application entrypoint.

The Assignment Helper stores transcripts alongside the Grammar Helper within
the shared ``falowen_chats`` collection. Keeping both experiences in the same
document allows the application to preload chats efficiently while maintaining
separate metadata fields for each helper.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import logging

try:  # Firestore is optional in local/test environments
    from firebase_admin import firestore
except Exception:  # pragma: no cover - Firestore may be unavailable in tests
    firestore = None  # type: ignore


_CHAT_FIELD = "assignment_helper"
_META_FIELD = "assignment_helper_meta"
_CHAT_COLLECTION = "falowen_chats"
_THREAD_COLLECTION = "assignment_helper_threads"


def _coerce_messages(value: Any) -> List[Dict[str, Any]]:
    """Return ``value`` as a list of assignment helper messages."""

    if isinstance(value, list):
        return [dict(item) if isinstance(item, dict) else item for item in value]
    return []


def get_assignment_helper_doc(db: Any, student_code: str):
    """Return the Firestore document reference for assignment helper chats."""

    if db is None or not student_code:
        return None
    try:
        return db.collection(_CHAT_COLLECTION).document(student_code)
    except Exception as exc:  # pragma: no cover - SDK failures are rare
        logging.warning(
            "Failed to resolve Assignment Helper doc for %s: %s", student_code, exc
        )
        return None


def load_assignment_helper_state(
    db: Any, student_code: str
) -> Tuple[Any, List[Dict[str, Any]], Dict[str, Any]]:
    """Return ``(doc_ref, messages, meta)`` for a student's assignment chat."""

    doc_ref = get_assignment_helper_doc(db, student_code)
    if doc_ref is None:
        return None, [], {}

    try:
        snapshot = doc_ref.get()
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        logging.warning(
            "Failed to load Assignment Helper transcript for %s: %s", student_code, exc
        )
        return doc_ref, [], {}

    data: Dict[str, Any] = {}
    if getattr(snapshot, "exists", False):
        try:
            data = snapshot.to_dict() or {}
        except Exception as exc:  # pragma: no cover - unexpected snapshot state
            logging.warning(
                "Assignment Helper snapshot conversion failed for %s: %s",
                student_code,
                exc,
            )
            data = {}

    chats = data.get("chats") if isinstance(data, dict) else {}
    raw_messages = chats.get(_CHAT_FIELD) if isinstance(chats, dict) else []
    messages = _coerce_messages(raw_messages)

    raw_meta = data.get(_META_FIELD)
    meta = raw_meta if isinstance(raw_meta, dict) else {}

    return doc_ref, messages, meta


def persist_assignment_helper_state(
    doc_ref: Any,
    *,
    messages: Iterable[Dict[str, Any]],
    level: Any = None,
    thread_id: Any = None,
    student_code: Any = None,
) -> bool:
    """Persist the latest Assignment Helper state to Firestore."""

    if doc_ref is None:
        return False

    message_list = list(messages or [])

    meta: Dict[str, Any] = {}
    if level is not None:
        meta["level"] = str(level)
    if thread_id is not None:
        thread_token = str(thread_id).strip()
        if thread_token:
            meta["thread_id"] = thread_token
    if student_code is not None:
        code_token = str(student_code).strip()
        if code_token:
            meta["student_code"] = code_token
    meta["message_count"] = len(message_list)

    server_timestamp = getattr(firestore, "SERVER_TIMESTAMP", None)
    if server_timestamp is not None:
        meta["updated_at"] = server_timestamp

    payload = {
        "chats": {_CHAT_FIELD: message_list},
        _META_FIELD: meta,
    }

    try:
        doc_ref.set(payload, merge=True)
        return True
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        doc_id = getattr(doc_ref, "id", "<unknown>")
        logging.warning(
            "Failed to persist Assignment Helper transcript for %s: %s", doc_id, exc
        )
        return False


def record_assignment_helper_thread(
    db: Any,
    *,
    thread_id: Any,
    student_code: Any,
    level: Any = None,
    message_count: Any = None,
) -> bool:
    """Upsert a summary record for a unique Assignment Helper thread."""

    if db is None:
        return False

    thread_token = str(thread_id or "").strip()
    if not thread_token:
        return False

    try:
        doc_ref = db.collection(_THREAD_COLLECTION).document(thread_token)
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        logging.warning(
            "Failed to resolve Assignment Helper thread doc for %s: %s",
            thread_token,
            exc,
        )
        return False

    payload: Dict[str, Any] = {
        "thread_id": thread_token,
        "student_code": str(student_code or "").strip(),
    }

    if level is not None:
        payload["level"] = str(level)

    try:
        count_value = int(message_count or 0)
    except Exception:
        count_value = 0
    payload["message_count"] = max(0, count_value)

    server_timestamp = getattr(firestore, "SERVER_TIMESTAMP", None)

    try:
        snapshot = doc_ref.get()
    except Exception:
        snapshot = None
    exists = bool(getattr(snapshot, "exists", False))

    if server_timestamp is not None:
        payload["updated_at"] = server_timestamp
        if not exists:
            payload["created_at"] = server_timestamp

    try:
        doc_ref.set(payload, merge=True)
        return True
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        logging.warning(
            "Failed to record Assignment Helper thread %s: %s",
            thread_token,
            exc,
        )
        return False


def clear_assignment_helper_state(doc_ref: Any) -> bool:
    """Remove the Assignment Helper transcript for the given document."""

    if doc_ref is None:
        return False

    try:
        delete_field = getattr(firestore, "DELETE_FIELD", None)
        if delete_field is None:
            doc_ref.set(
                {
                    "chats": {_CHAT_FIELD: []},
                    _META_FIELD: {},
                },
                merge=True,
            )
        else:
            doc_ref.set(
                {
                    "chats": {_CHAT_FIELD: delete_field},
                    _META_FIELD: delete_field,
                },
                merge=True,
            )
        return True
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        doc_id = getattr(doc_ref, "id", "<unknown>")
        logging.warning(
            "Failed to clear Assignment Helper transcript for %s: %s", doc_id, exc
        )
        return False

