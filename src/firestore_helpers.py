"""Utility helpers for Firestore interaction used by the main app.

These helpers were previously embedded in ``a1sprechen.py`` but moving them
here keeps the entrypoint slimmer and improves reusability.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter

try:  # Firestore-specific exceptions may be unavailable in tests
    from google.api_core import exceptions as google_exceptions
except Exception:  # pragma: no cover - optional dependency
    google_exceptions = None  # type: ignore[assignment]

try:  # Firestore may be unavailable in tests
    from falowen.sessions import get_db
except Exception:  # pragma: no cover - missing sessions stub
    def get_db():  # type: ignore
        return None

db = None  # type: ignore


def _get_db():
    return db if db is not None else get_db()


if google_exceptions is not None:  # pragma: no cover - depends on optional import
    FIRESTORE_ORDERING_ERRORS: Tuple[type, ...] = (
        google_exceptions.FailedPrecondition,
        google_exceptions.InvalidArgument,
        google_exceptions.OutOfRange,
        google_exceptions.GoogleAPICallError,
    )
else:  # pragma: no cover - fallback when google api core is absent
    FIRESTORE_ORDERING_ERRORS = (Exception,)


def _coerce_timestamp(value: Any) -> float:
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def stream_latest_snapshots(query, timestamp_field: str, *, limit: Optional[int] = None) -> List[Tuple[Any, Dict[str, Any]]]:
    """Return snapshots ordered by ``timestamp_field`` (newest first).

    Firestore requires specific composite indexes for ordered queries. When the
    server reports ``FailedPrecondition`` or a similar error, we retry without
    the ``order_by`` clause and sort client-side to maintain behaviour.
    """

    try:
        ordered = query.order_by(timestamp_field, direction=firestore.Query.DESCENDING)
        if limit is not None:
            ordered = ordered.limit(limit)
        snapshots = list(ordered.stream())
        return [(snap, snap.to_dict() or {}) for snap in snapshots]
    except FIRESTORE_ORDERING_ERRORS:
        try:
            fallback_snaps = list(query.stream())
        except Exception:
            return []

        items: List[Tuple[Any, Dict[str, Any]]] = []
        for snap in fallback_snaps:
            data = snap.to_dict() or {}
            items.append((snap, data))

        items.sort(key=lambda item: _coerce_timestamp(item[1].get(timestamp_field)), reverse=True)
        if limit is not None:
            return items[:limit]
        return items
from src.firestore_utils import load_draft_meta_from_db


def lesson_key_build(level: str, day: int, chapter: str) -> str:
    """Unique, safe key for this lesson (reusable in docs/fields)."""
    safe_ch = re.sub(r"[^A-Za-z0-9_\-]+", "_", str(chapter))
    return f"{level}_day{day}_ch{safe_ch}"


def lock_id(level: str, code: str, lesson_key: str) -> str:
    """Stable document id for submission lock."""
    safe_code = re.sub(r"[^A-Za-z0-9_\-]+", "_", str(code))
    return f"{level}__{safe_code}__{lesson_key}"


def has_existing_submission(level: str, code: str, lesson_key: str) -> bool:
    """True if a submission exists for this (level, code, lesson_key)."""
    db = _get_db()
    posts_ref = db.collection("submissions").document(level).collection("posts")
    try:
        q = (
            posts_ref.where(filter=FieldFilter("student_code", "==", code))
            .where(filter=FieldFilter("lesson_key", "==", lesson_key))
            .limit(1)
            .stream()
        )
        return any(True for _ in q)
    except Exception:
        try:
            for _ in (
                posts_ref.where(filter=FieldFilter("student_code", "==", code))
                .where(filter=FieldFilter("lesson_key", "==", lesson_key))
                .stream()
            ):
                return True
        except Exception:
            pass
        return False


def acquire_lock(level: str, code: str, lesson_key: str) -> bool:
    """Create a lock doc; if it already exists, treat as locked."""
    db = _get_db()
    ref = db.collection("submission_locks").document(lock_id(level, code, lesson_key))
    try:
        ref.create(
            {
                "level": level,
                "student_code": code,
                "lesson_key": lesson_key,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return True
    except Exception:
        try:
            exists = ref.get().exists
            if exists:
                return False
            ref.set(
                {
                    "level": level,
                    "student_code": code,
                    "lesson_key": lesson_key,
                    "created_at": firestore.SERVER_TIMESTAMP,
                },
                merge=False,
            )
            return True
        except Exception:
            return False


def is_locked(level: str, code: str, lesson_key: str) -> bool:
    """Treat either an existing submission OR a lock doc as 'locked'."""
    if has_existing_submission(level, code, lesson_key):
        return True
    db = _get_db()
    try:
        ref = db.collection("submission_locks").document(lock_id(level, code, lesson_key))
        return ref.get().exists
    except Exception:
        return False


def resolve_current_content(level: str, code: str, lesson_key: str, draft_key: str) -> dict:
    """Determine what content should be displayed for the lesson editor."""
    latest = fetch_latest(level, code, lesson_key)
    if latest:
        return {
            "text": latest.get("answer", "") or "",
            "ts": latest.get("updated_at"),
            "status": "submitted",
            "locked": True,
            "source": "submission",
        }

    draft_text, draft_ts = load_draft_meta_from_db(code, draft_key)
    if draft_text:
        return {
            "text": draft_text,
            "ts": draft_ts,
            "status": "draft",
            "locked": False,
            "source": "draft",
        }

    return {
        "text": "",
        "ts": None,
        "status": "empty",
        "locked": False,
        "source": "empty",
    }


def fetch_latest(level: str, code: str, lesson_key: str) -> Optional[Dict[str, Any]]:
    """Fetch the most recent submission for this user/lesson (or ``None``)."""
    db = _get_db()
    posts_ref = db.collection("submissions").document(level).collection("posts")
    base_query = (
        posts_ref.where(filter=FieldFilter("student_code", "==", code))
        .where(filter=FieldFilter("lesson_key", "==", lesson_key))
    )
    docs = stream_latest_snapshots(base_query, "updated_at", limit=1)
    return docs[0][1] if docs else None


__all__ = [
    "lesson_key_build",
    "lock_id",
    "has_existing_submission",
    "acquire_lock",
    "is_locked",
    "resolve_current_content",
    "fetch_latest",
    "stream_latest_snapshots",
]
