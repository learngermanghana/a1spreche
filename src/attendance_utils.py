"""Utilities for retrieving classroom attendance data.

This module isolates the Firestore queries needed to determine a student's
attendance history for a class.  Keeping the logic here makes it easier to
unit-test without touching the Streamlit UI or the large ``a1sprechen``
module.
"""

from __future__ import annotations

from typing import List, Dict, Tuple
import logging

try:  # Firestore client is optional in test environments
    from falowen.sessions import db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - Firestore may be unavailable
    db = None  # type: ignore


def load_attendance_records(
    student_code: str, class_name: str
) -> Tuple[List[Dict[str, object]], int, float]:
    """Return a tuple ``(records, sessions, hours)`` for ``student_code``.

    Each record in ``records`` is a mapping with ``{"session": <id>,
    "present": <bool>}``.  ``sessions`` is the number of sessions attended and
    ``hours`` is the invested time assuming **1 hour per attended session**.

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
        for snap in sessions_ref.stream():
            data = snap.to_dict() or {}
            attendees = data.get("attendees", {}) or {}
            present = False
            if isinstance(attendees, dict):
                present = student_code in attendees
            elif isinstance(attendees, list):
                present = any(
                    isinstance(item, dict) and item.get("code") == student_code
                    for item in attendees
                )
            records.append({"session": getattr(snap, "id", ""), "present": present})
            if present:
                count += 1
        hours = float(count)
        return records, count, hours
    except Exception as exc:  # pragma: no cover - runtime depends on Firestore
        logging.exception(
            "Failed to load attendance for %s/%s: %s", class_name, student_code, exc
        )
        return [], 0, 0.0

