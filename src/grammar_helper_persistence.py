"""Helpers for persisting Grammar Helper chat transcripts in Firestore.

This module mirrors the lightweight persistence helpers that exist for other
chat-based experiences (for example :mod:`src.topic_coach_persistence`).  It is
kept deliberately small and dependency free so that unit tests can exercise the
logic without importing the full Streamlit application entrypoint.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import logging

try:  # Firestore is optional in local/test environments
    from firebase_admin import firestore
except Exception:  # pragma: no cover - Firestore may be unavailable in tests
    firestore = None  # type: ignore


_CHAT_FIELD = "grammar_helper"
_META_FIELD = "grammar_helper_meta"
_COLLECTION = "falowen_chats"


def _coerce_messages(value: Any) -> List[Dict[str, Any]]:
    """Return ``value`` as a list of grammar helper messages."""

    if isinstance(value, list):
        return [dict(item) if isinstance(item, dict) else item for item in value]
    return []


def get_grammar_helper_doc(db: Any, student_code: str):
    """Return the Firestore document reference for Grammar Helper chats."""

    if db is None or not student_code:
        return None
    try:
        return db.collection(_COLLECTION).document(student_code)
    except Exception as exc:  # pragma: no cover - SDK failures are rare
        logging.warning(
            "Failed to resolve Grammar Helper doc for %s: %s", student_code, exc
        )
        return None


def load_grammar_helper_state(
    db: Any, student_code: str
) -> Tuple[Any, List[Dict[str, Any]], Dict[str, Any]]:
    """Return ``(doc_ref, messages, meta)`` for a student's Grammar Helper chat."""

    doc_ref = get_grammar_helper_doc(db, student_code)
    if doc_ref is None:
        return None, [], {}

    try:
        snapshot = doc_ref.get()
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        logging.warning(
            "Failed to load Grammar Helper transcript for %s: %s", student_code, exc
        )
        return doc_ref, [], {}

    data: Dict[str, Any] = {}
    if getattr(snapshot, "exists", False):
        try:
            data = snapshot.to_dict() or {}
        except Exception as exc:  # pragma: no cover - unexpected snapshot state
            logging.warning(
                "Grammar Helper snapshot conversion failed for %s: %s",
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


def persist_grammar_helper_state(
    doc_ref: Any,
    *,
    messages: Iterable[Dict[str, Any]],
    level: Any = None,
    student_code: Any = None,
) -> bool:
    """Persist the latest Grammar Helper state to Firestore."""

    if doc_ref is None:
        return False

    message_list = list(messages or [])

    meta: Dict[str, Any] = {}
    if level is not None:
        meta["level"] = str(level)
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
            "Failed to persist Grammar Helper transcript for %s: %s", doc_id, exc
        )
        return False


def clear_grammar_helper_state(doc_ref: Any) -> bool:
    """Clear the stored Grammar Helper chat transcript for ``doc_ref``."""

    if doc_ref is None:
        return False

    delete_sentinel = getattr(firestore, "DELETE_FIELD", None)
    if delete_sentinel is None:
        payload = {"chats": {_CHAT_FIELD: []}, _META_FIELD: {}}
    else:
        payload = {
            "chats": {_CHAT_FIELD: delete_sentinel},
            _META_FIELD: delete_sentinel,
        }

    try:
        doc_ref.set(payload, merge=True)
        return True
    except Exception as exc:  # pragma: no cover - depends on Firestore availability
        doc_id = getattr(doc_ref, "id", "<unknown>")
        logging.warning(
            "Failed to clear Grammar Helper transcript for %s: %s", doc_id, exc
        )
        return False
