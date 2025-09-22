"""Utility helpers for Firestore interaction used by the main app.

These helpers were previously embedded in ``a1sprechen.py`` but moving them
here keeps the entrypoint slimmer and improves reusability.
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from firebase_admin import firestore

try:  # FieldFilter is optional for environments without Firestore client
    from google.cloud.firestore_v1 import FieldFilter
except ImportError:  # pragma: no cover - fallback exercised in tests
    FieldFilter = None  # type: ignore[assignment]

try:  # Firestore may be unavailable in tests
    from falowen.sessions import get_db
except Exception:  # pragma: no cover - missing sessions stub
    def get_db():  # type: ignore
        return None

db = None  # type: ignore


def _get_db():
    return db if db is not None else get_db()


def _firestore_where(query, field: str, op: str, value):
    """Apply a ``where`` clause supporting optional ``FieldFilter`` imports."""

    if FieldFilter is None:
        return query.where(field, op, value)
    return query.where(filter=FieldFilter(field, op, value))
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
        query = _firestore_where(posts_ref, "student_code", "==", code)
        query = _firestore_where(query, "lesson_key", "==", lesson_key)
        q = query.limit(1).stream()
        return any(True for _ in q)
    except Exception:
        try:
            query = _firestore_where(posts_ref, "student_code", "==", code)
            query = _firestore_where(query, "lesson_key", "==", lesson_key)
            for _ in query.stream():
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
    try:
        query = _firestore_where(posts_ref, "student_code", "==", code)
        query = _firestore_where(query, "lesson_key", "==", lesson_key)
        docs = (
            query.order_by("updated_at", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        for d in docs:
            return d.to_dict()
    except Exception:
        try:
            query = _firestore_where(posts_ref, "student_code", "==", code)
            query = _firestore_where(query, "lesson_key", "==", lesson_key)
            docs = query.stream()
            items = [d.to_dict() for d in docs]
            items.sort(key=lambda x: x.get("updated_at"), reverse=True)
            return items[0] if items else None
        except Exception:
            return None
    return None


def _coerce_score_value(value: Any) -> Optional[float]:
    """Best-effort conversion of a score value to ``float``."""

    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            if math.isnan(value):  # type: ignore[arg-type]
                return None
        except Exception:
            pass
        try:
            return float(value)
        except Exception:
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        text = text.replace("%", "")
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if match:
            try:
                return float(match.group())
            except Exception:
                return None
    return None


def _score_timestamp(value: Any) -> float:
    """Return a comparable timestamp for ordering score documents."""

    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except Exception:
            return 0.0
    if isinstance(value, datetime):
        try:
            return float(value.timestamp())
        except Exception:
            return 0.0
    try:
        if hasattr(value, "timestamp"):
            return float(value.timestamp())  # type: ignore[call-arg]
    except Exception:
        pass
    return 0.0


def _score_matches_lesson(doc: Dict[str, Any], lesson_key: str) -> bool:
    key_norm = (lesson_key or "").strip().lower()
    if not key_norm:
        return False
    for field in ("lesson_key", "lessonKey", "lesson", "chapter"):
        value = doc.get(field)
        if value is None:
            continue
        text = str(value).strip().lower()
        if text == key_norm:
            return True
    return False


def _score_candidates(ref, filters: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    try:
        query = ref
        for field, value in filters.items():
            query = _firestore_where(query, field, "==", value)
        docs = [doc.to_dict() for doc in query.stream()]
    except Exception:
        return []

    docs.sort(
        key=lambda item: _score_timestamp(
            item.get("updated_at")
            or item.get("graded_at")
            or item.get("created_at")
        ),
        reverse=True,
    )
    return docs


def fetch_latest_score(
    student_code: str,
    lesson_key: str,
    submission: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent score document for this lesson.

    The helper first tries to match on explicit submission identifiers before
    falling back to ``student_code``/``lesson_key`` pairs. The returned
    dictionary contains the original document data plus a ``numeric_score`` key
    when a numeric value could be inferred.
    """

    db = _get_db()
    if db is None:
        return None

    try:
        scores_ref = db.collection("scores")
    except Exception:
        return None

    candidates: list[Dict[str, Any]] = []

    def _extend_from(filters: Dict[str, Any]) -> None:
        for doc in _score_candidates(scores_ref, filters):
            candidates.append(doc)

    submission_ids: list[str] = []
    if submission:
        for key in (
            "submission_id",
            "submissionId",
            "submission_doc_id",
            "submission",
            "id",
            "doc_id",
        ):
            value = submission.get(key)
            if value:
                text = str(value).strip()
                if text:
                    submission_ids.append(text)

    for sid in submission_ids:
        for field in ("submission_id", "submissionId", "submission_doc_id"):
            _extend_from({field: sid})
        if candidates:
            break

    student_code = (student_code or "").strip()
    lesson_key = (lesson_key or "").strip()

    if not candidates and student_code and lesson_key:
        for code_field in ("student_code", "studentCode", "studentcode"):
            for lesson_field in ("lesson_key", "lessonKey"):
                _extend_from({code_field: student_code, lesson_field: lesson_key})
            if candidates:
                break

    if not candidates and student_code:
        for code_field in ("student_code", "studentCode", "studentcode"):
            for doc in _score_candidates(scores_ref, {code_field: student_code}):
                if lesson_key and _score_matches_lesson(doc, lesson_key):
                    candidates.append(doc)
            if candidates:
                break

    if not candidates:
        return None

    best = candidates[0]
    payload = dict(best)

    numeric_score: Optional[float] = None
    for key in (
        "numeric_score",
        "score",
        "percentage",
        "percent",
        "points",
        "marks",
    ):
        numeric_score = _coerce_score_value(payload.get(key))
        if numeric_score is not None:
            break
    if numeric_score is not None:
        payload["numeric_score"] = numeric_score

    status_value = payload.get("status") or payload.get("status_text")
    if isinstance(status_value, str):
        payload["status_text"] = status_value.strip()

    return payload


__all__ = [
    "lesson_key_build",
    "lock_id",
    "has_existing_submission",
    "acquire_lock",
    "is_locked",
    "resolve_current_content",
    "fetch_latest",
    "fetch_latest_score",
]
