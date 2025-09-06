"""Utilities for retrieving classroom attendance data.

This module isolates the Firestore queries needed to determine a student's
attendance history for a class.  Keeping the logic here makes it easier to
unit-test without touching the Streamlit UI or the large ``a1sprechen``
module.
"""

from __future__ import annotations

from typing import List, Dict, Tuple
import logging

from .firestore_utils import format_record

try:  # Firestore client is optional in test environments
    from falowen.sessions import db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - Firestore may be unavailable
    db = None  # type: ignore


def load_attendance_records(
    student_code: str, class_name: str
) -> Tuple[List[Dict[str, object]], int, float]:
    """Return a tuple ``(records, sessions, hours)`` for ``student_code``.

    Each record in ``records`` is a mapping with ``{"session": <label>,
    "present": <bool>}`` where ``label`` is a normalised session title.  ``sessions``
    is the number of sessions attended and ``hours`` is the invested time based on
    the Firestore record (defaulting to **1 hour** when unspecified).

    If Firestore is unavailable or an error occurs the function returns
    ``([], 0, 0.0)``.
    """

    if db is None:
        return [], 0, 0.0

    try:
        sessions_ref = (
            db.collection("attendance")
            .document(class_name)
            .collection("sessions")
        )
        records: List[Dict[str, object]] = []
        count = 0
        hours = 0.0
        for snap in sessions_ref.stream():
            data = snap.to_dict() or {}
            record, session_hours = format_record(getattr(snap, "id", ""), data, student_code)
            records.append(record)
            if record["present"]:
                count += 1
                hours += session_hours

        return records, count, hours
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception(
            "Failed to load attendance for %s/%s: %s", class_name, student_code, exc
        )
        return [], 0, 0.0

