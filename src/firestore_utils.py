"""Firestore-related helper functions for the a1spreche app.

This module centralises Firestore draft and chat helpers so they can be
re-used outside the monolithic :mod:`a1sprechen` module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import logging
import re
from firebase_admin import firestore
from rapidfuzz import fuzz, process

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
    CANONICAL_LABELS: list[str] = []


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
    from falowen.sessions import db  # pragma: no cover - runtime side effect
    try:
        # Touch the ``students`` collection to ensure it is available.  This
        # avoids surprising ``AttributeError`` if Firestore was partially
        # initialised but the collection is missing.  No network call is made.
        db.collection("students")
    except Exception:  # pragma: no cover - Firestore may be unavailable
        pass
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


def load_student_profile(code: str) -> str:
    """Return the stored 'about' text for ``code``."""

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


def fetch_attendance_summary(student_code: str, class_name: str) -> tuple[int, float]:
    """Return ``(sessions, hours)`` attended by ``student_code`` in ``class_name``.

    The data is expected under ``attendance/{class_name}/sessions`` where each
    session document contains an ``attendees`` or ``students`` mapping of
    student codes to hours attended.  If Firestore is unavailable or an error
    occurs, ``(0, 0.0)`` is returned.
    """

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

