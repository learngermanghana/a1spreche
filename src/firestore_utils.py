"""Firestore-related helper functions for the a1spreche app.

Roster data is sourced from the CSV roster during login and is stored in
``st.session_state['student_row']``.  The helpers in this module only deal
with dynamic data such as submissions, drafts, attendance records or chat
profiles and never query Firestore for static roster metadata like class names
or levels.

This module centralises Firestore draft and chat helpers so they can be
re-used outside the monolithic :mod:`a1sprechen` module.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import logging
import re
from firebase_admin import firestore
from rapidfuzz import fuzz, process
from google.cloud.firestore_v1 import FieldFilter

# Build a canonical list of exercise labels used across the platform.  This
# allows us to fuzzy-match noisy user-facing titles to their official version.
try:  # pragma: no cover - schedule/streamlit may be unavailable in some tests
    from .schedule import get_a1_schedule

    CANONICAL_LABELS = sorted(
        {
            item.get("topic", "")
            for item in get_a1_schedule()  # type: ignore[func-returns-value]
            if item.get("topic")
        }
    )
except Exception:  # pragma: no cover - best effort for offline tests
    CANONICAL_LABELS: List[str] = []


def normalize_label(label: str) -> str:
    """Return a cleaned exercise label.

    Removes any leading ``"Woche X:"`` prefix and attempts to fuzzy-match the
    remainder against :data:`CANONICAL_LABELS`.  If no sufficiently close match
    is found the cleaned label is returned unchanged.
    """

    if not label:
        return ""

    cleaned = re.sub(r"^Woche\s*\d+\s*:\s*", "", label, flags=re.I).strip()
    if not CANONICAL_LABELS:
        return cleaned

    match = process.extractOne(
        cleaned,
        CANONICAL_LABELS,
        scorer=fuzz.ratio,
        score_cutoff=80,
    )
    return match[0] if match else cleaned


def format_record(doc_id: str, data: Dict[str, Any], student_code: str) -> Tuple[Dict[str, object], float]:
    """Return a normalized attendance record and invested hours.

    ``data`` is the dictionary representation of a session document.  Attendance
    may be stored under an ``attendees`` or ``students`` mapping or as
    top-level keys.  The return value is a tuple ``(record, hours)`` where
    ``record`` is suitable for display in the UI and ``hours`` indicates the
    invested time for the student.  The ``record`` mapping contains
    ``{"session": <label>, "present": <bool>}``.
    """

    attendees = data.get("attendees") or data.get("students") or data
    label = normalize_label(data.get("label") or doc_id)

    present = False
    session_hours = 0.0

    if isinstance(attendees, dict):
        entry = attendees.get(student_code)
        if isinstance(entry, dict):
            present = bool(entry.get("present"))
            if present:
                try:
                    session_hours = float(entry.get("hours", 1) or 0)
                except Exception:
                    session_hours = 1.0
        elif isinstance(entry, (int, float, bool)):
            present = bool(entry)
            if present:
                try:
                    session_hours = float(entry)
                except Exception:
                    session_hours = 1.0
    elif isinstance(attendees, list):
        present = any(
            isinstance(item, dict) and item.get("code") == student_code
            for item in attendees
        )
        if present:
            session_hours = 1.0

    return {"session": label, "present": present}, session_hours

try:  # Firestore client is optional in test environments
    from falowen.sessions import get_db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - Firestore may be unavailable
    def get_db():  # type: ignore
        return None

db = None  # type: ignore

_TYPING_TTL_SECONDS = 10.0


def _ensure_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _get_db():
    return db if db is not None else get_db()


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

    db = _get_db()
    if db is None:
        return None
    return (
        db.collection("drafts_v2")
        .document(code)
        .collection("lessons")
        .document(lesson_key)
    )


def _typing_collection(level: str, class_code: str, qid: str):
    db = _get_db()
    if db is None:
        return None
    return (
        db.collection("class_board")
        .document(level)
        .collection("classes")
        .document(class_code)
        .collection("posts")
        .document(qid)
        .collection("typing")
    )


def _typing_doc_ref(level: str, class_code: str, qid: str, student_code: str):
    collection = _typing_collection(level, class_code, qid)
    if collection is None:
        return None
    return collection.document(student_code)


def set_typing_indicator(
    level: str,
    class_code: str,
    qid: str,
    student_code: str,
    student_name: str,
    *,
    is_typing: bool,
    now: Optional[datetime] = None,
) -> bool:
    """Update the typing indicator state for a class board draft."""

    if not (level and class_code and qid and student_code):
        return False

    doc_ref = _typing_doc_ref(level, class_code, qid, student_code)
    if doc_ref is None:
        return False

    try:
        if is_typing:
            ts = _ensure_utc(now or datetime.now(timezone.utc))
            doc_ref.set(
                {
                    "student_name": student_name or "",
                    "last_seen": ts,
                }
            )
        else:
            doc_ref.delete()
    except Exception as exc:  # pragma: no cover - network failures best-effort
        logging.debug(
            "Failed to update typing indicator for %s/%s/%s: %s",
            level,
            class_code,
            qid,
            exc,
        )
        return False

    return True


def _coerce_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return _ensure_utc(value)
    if hasattr(value, "to_datetime"):
        try:
            return _ensure_utc(value.to_datetime())
        except Exception:
            return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), timezone.utc)
        except Exception:
            return None
    return None


def fetch_active_typists(
    level: str,
    class_code: str,
    qid: str,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: float = _TYPING_TTL_SECONDS,
) -> List[Dict[str, Any]]:
    """Return active typing indicators for ``qid`` filtered by ``ttl_seconds``."""

    if ttl_seconds <= 0:
        ttl_seconds = _TYPING_TTL_SECONDS

    collection = _typing_collection(level, class_code, qid)
    if collection is None:
        return []

    current_time = _ensure_utc(now or datetime.now(timezone.utc))
    cutoff = current_time - timedelta(seconds=ttl_seconds)
    try:
        snapshots = list(collection.stream())
    except Exception as exc:  # pragma: no cover - Firestore best-effort
        logging.debug(
            "Failed to read typing indicators for %s/%s/%s: %s",
            level,
            class_code,
            qid,
            exc,
        )
        return []

    active: List[Dict[str, Any]] = []
    for snap in snapshots:
        try:
            data = snap.to_dict() or {}
        except Exception:
            continue
        ts = _coerce_timestamp(data.get("last_seen"))
        if ts is None or ts < cutoff:
            continue
        entry = {
            "student_code": getattr(snap, "id", ""),
            "student_name": data.get("student_name", ""),
            "last_seen": ts,
        }
        active.append(entry)

    return active


# ---- Draft lookups ---------------------------------------------------------


def recover_student_code_from_drafts(
    lesson_key: str,
    *,
    draft_text: Optional[str] = None,
) -> Optional[str]:
    """Best-effort lookup of the student code for ``lesson_key`` drafts.

    This performs a collection-group query across ``drafts_v2/*/lessons`` and
    returns the ``student_code`` of the most recently updated draft that
    matches ``lesson_key``.  When ``draft_text`` is provided the search is
    further narrowed to drafts whose ``text`` matches the local contents.  The
    lookup gracefully degrades when Firestore is unavailable or when indexes
    are missing by falling back to client-side sorting.
    """

    if not lesson_key:
        return None

    db = _get_db()
    if db is None:
        return None

    try:
        query = db.collection_group("lessons").where(
            filter=FieldFilter("lesson_key", "==", lesson_key)
        )
        if draft_text:
            query = query.where(filter=FieldFilter("text", "==", str(draft_text)))

        try:
            snapshots = list(
                query.order_by("updated_at", direction=firestore.Query.DESCENDING)
                .limit(5)
                .stream()
            )
        except Exception:
            snapshots = list(query.stream())

    except Exception as exc:  # pragma: no cover - Firestore runtime dependency
        logging.debug("Failed to query drafts for %s: %s", lesson_key, exc)
        return None

    if not snapshots:
        return None

    def _snapshot_ts(snap) -> float:
        try:
            data = snap.to_dict() or {}
        except Exception:
            return 0.0
        ts = data.get("updated_at")
        if isinstance(ts, datetime):
            try:
                return ts.timestamp()
            except Exception:
                return 0.0
        if isinstance(ts, (int, float)):
            try:
                return float(ts)
            except Exception:
                return 0.0
        return 0.0

    try:
        snapshots.sort(key=_snapshot_ts, reverse=True)
    except Exception:
        pass

    for snap in snapshots:
        try:
            data = snap.to_dict() or {}
        except Exception:
            data = {}
        candidate = data.get("student_code")
        if not candidate:
            try:
                parent = snap.reference.parent
                if parent is not None:
                    owner = parent.parent
                    if owner is not None:
                        candidate = owner.id
            except Exception:
                candidate = None
        if candidate:
            candidate_str = str(candidate).strip()
            if candidate_str and candidate_str.lower() != "demo001":
                return candidate_str

    return None


# ---- DRAFTS (server-side) — now stored separately from submissions ----

def save_draft_to_db(code: str, field_key: str, text: str) -> None:
    """Persist the given ``text`` as a draft for ``code``/``field_key``."""

    db = _get_db()
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

    db = _get_db()
    if db is None:
        return
    ref = db.collection("falowen_chats").document(code)
    mode_level_teil = conv_key.rsplit("_", 1)[0]
    try:
        updates = {"current_conv": {mode_level_teil: conv_key}}
        if text:
            updates["drafts"] = {conv_key: text}
        else:
            updates["drafts"] = {conv_key: firestore.DELETE_FIELD}
        ref.set(updates, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save chat draft for %s/%s: %s", code, conv_key, exc)
        return


def load_chat_draft_from_db(code: str, conv_key: str) -> str:
    """Retrieve any saved chat draft for the conversation."""

    db = _get_db()
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


def save_student_profile(code: str, about: str) -> None:
    """Persist a student's profile information."""

    db = _get_db()
    if db is None:
        return
    if not code:
        return
    ref = db.collection("students").document(code)
    payload = {
        "about": about or "",
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    try:
        ref.set(payload, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save student profile for %s: %s", code, exc)


def delete_student_profile(code: str) -> None:
    """Remove the ``about`` field for ``code``'s profile."""

    db = _get_db()
    if db is None:
        return
    if not code:
        return
    ref = db.collection("students").document(code)
    try:
        ref.set({"about": firestore.DELETE_FIELD}, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to delete student profile for %s: %s", code, exc)


def load_student_profile(code: str) -> str:
    """Return the stored 'about' text for ``code``."""

    db = _get_db()
    if db is None:
        return ""
    try:
        snap = db.collection("students").document(code).get()
        if snap.exists:
            data = snap.to_dict() or {}
            return data.get("about", "") or ""
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception("Failed to load student profile for %s: %s", code, exc)
    return ""


def load_draft_meta_from_db(code: str, field_key: str) -> Tuple[str, Optional[datetime]]:
    """Return ``(text, updated_at)`` for the requested draft."""
    db = _get_db()
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


def save_ai_answer(post_id: str, ai_text: str, flagged: bool = False) -> None:
    """Attach an AI-generated suggestion to the post."""

    db = _get_db()
    if db is None:
        return
    ref = db.collection("qa_posts").document(post_id)
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


def save_ai_response(post_id: str, ai_text: str, flagged: bool = False) -> None:
    """Attach an AI-generated reply suggestion to the post."""

    db = _get_db()
    if db is None:
        return
    ref = db.collection("qa_posts").document(post_id)
    payload = {
        "ai_response_suggestion": ai_text,
        "ai_response_created_at": firestore.SERVER_TIMESTAMP,
    }
    if flagged:
        payload["flagged"] = True
    try:
        ref.set(payload, merge=True)
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.warning("Failed to save AI response for %s: %s", post_id, exc)


def save_response(post_id: str, text: str, responder_code: str) -> None:
    """Persist a response for a post.

    The response is appended to the ``responses`` array on the post and
    includes the ``responder_code`` and server timestamp.
    """

    db = _get_db()
    if db is None:
        return
    ref = db.collection("qa_posts").document(post_id)
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


def fetch_attendance_summary(student_code: str, class_name: str) -> Tuple[int, float]:
    """Return ``(sessions, hours)`` attended by ``student_code`` in ``class_name``.

    The data is expected under ``attendance/{class_name}/sessions`` where each
    session document contains an ``attendees`` or ``students`` mapping of
    student codes to hours attended.  If Firestore is unavailable or an error
    occurs, ``(0, 0.0)`` is returned.
    """

    db = _get_db()
    if db is None:
        return 0, 0.0

    try:
        sessions_ref = (
            db.collection("attendance")
            .document(class_name)
            .collection("sessions")
        )
        student_code_norm = student_code.strip().lower()
        count = 0
        hours = 0.0
        for snap in sessions_ref.stream():
            data = snap.to_dict() or {}
            if "attendees" in data:
                attendees = data.get("attendees") or {}
            elif "students" in data:
                attendees = data.get("students") or {}
            else:
                attendees = data
            if isinstance(attendees, dict):
                attendees_norm = {
                    str(k).strip().lower(): v for k, v in attendees.items()
                }
                entry = attendees_norm.get(student_code_norm)
                if isinstance(entry, dict) and "present" in entry:
                    if bool(entry.get("present")):
                        count += 1
                        try:
                            hours += float(entry.get("hours", 1) or 0)
                        except Exception:
                            pass
                elif student_code_norm in attendees_norm:
                    count += 1
                    try:
                        hours += float(attendees_norm.get(student_code_norm, 0) or 0)
                    except Exception:
                        pass
            elif isinstance(attendees, list):
                for item in attendees:
                    if (
                        isinstance(item, dict)
                        and str(item.get("code", "")).strip().lower()
                        == student_code_norm
                        and bool(item.get("present", True))
                    ):
                        count += 1
                        try:
                            hours += float(item.get("hours", 0) or 0)
                        except Exception:
                            pass
                        break
        return count, hours
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception(
            "Failed to fetch attendance summary for %s/%s: %s",
            class_name,
            student_code,
            exc,
        )
        return 0, 0.0

