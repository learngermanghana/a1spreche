"""Persistence helpers for the Assignment Helper chat experience.

This module mirrors :mod:`src.topic_coach_persistence` but keeps the
implementation scoped to the Assignment Helper tab so that tests and other
callers can exercise the Firestore integration without importing the
Streamlit application entrypoint.
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
_COLLECTION = "assignment_helper_chats"


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
        return db.collection(_COLLECTION).document(student_code)
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
) -> bool:
    """Persist the latest Assignment Helper state to Firestore."""

    if doc_ref is None:
        return False

    meta: Dict[str, Any] = {}
    if level is not None:
        meta["level"] = str(level)

    server_timestamp = getattr(firestore, "SERVER_TIMESTAMP", None)
    if server_timestamp is not None:
        meta["updated_at"] = server_timestamp

    payload = {
        "chats": {_CHAT_FIELD: list(messages or [])},
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


def clear_assignment_helper_state(doc_ref: Any) -> bool:
    """Remove the Assignment Helper transcript for the given document."""

    if doc_ref is None:
        return False

    try:
        delete_field = getattr(firestore, "DELETE_FIELD", None)
        if delete_field is None:
            doc_ref.delete()
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

