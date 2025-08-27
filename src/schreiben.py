"""Helpers for Schreiben statistics, feedback, and usage tracking.

These utilities were previously defined inside ``a1sprechen.py`` but have been
extracted into their own module for easier reuse and testing.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Tuple

import streamlit as st
from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1 import FieldFilter
from firebase_admin import firestore

try:  # Firestore may be unavailable in tests
    from falowen.sessions import db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - handle missing Firestore gracefully
    db = None  # type: ignore


# ---------------------------------------------------------------------------
# Schreiben stats helpers
# ---------------------------------------------------------------------------


def update_schreiben_stats(student_code: str) -> None:
    """Recalculate stats for a student after each submission."""

    if not student_code:
        st.warning("No student code provided; skipping stats update.")
        return
    if db is None:
        st.warning("Firestore not initialized; skipping stats update.")
        return

    submissions = db.collection("schreiben_submissions").where(
        filter=FieldFilter("student_code", "==", student_code)
    ).stream()

    total = 0
    passed = 0
    scores = []
    last_letter = ""
    last_attempt = None

    for doc in submissions:
        data = doc.to_dict()
        total += 1
        score = data.get("score", 0)
        scores.append(score)
        if data.get("passed"):
            passed += 1
        last_letter = data.get("letter", "") or last_letter
        last_attempt = data.get("date", last_attempt)

    pass_rate = (passed / total * 100) if total > 0 else 0
    best_score = max(scores) if scores else 0
    average_score = sum(scores) / total if scores else 0

    stats_ref = db.collection("schreiben_stats").document(student_code)
    try:
        stats_ref.set(
            {
                "total": total,
                "passed": passed,
                "pass_rate": pass_rate,
                "best_score": best_score,
                "average_score": average_score,
                "last_attempt": last_attempt,
                "last_letter": last_letter,
                "attempts": scores,
            },
            merge=True,
        )
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to update Schreiben stats: {exc}")


def get_schreiben_stats(student_code: str):
    """Fetch Schreiben stats for a student from Firestore."""

    default_stats = {
        "total": 0,
        "passed": 0,
        "average_score": 0,
        "best_score": 0,
        "pass_rate": 0,
        "last_attempt": None,
        "attempts": [],
        "last_letter": "",
    }
    if not student_code:
        st.warning("No student code provided; cannot load stats.")
        return default_stats
    if db is None:
        st.warning("Firestore not initialized; cannot load stats.")
        return default_stats

    stats_ref = db.collection("schreiben_stats").document(student_code)

    try:
        doc = stats_ref.get()
    except GoogleAPICallError as exc:  # pragma: no cover - network failure
        logging.error("Failed to fetch schreiben stats: %s", exc)
        return default_stats

    if doc.exists:
        return doc.to_dict()
    return default_stats


# ---------------------------------------------------------------------------
# Schreiben feedback helpers
# ---------------------------------------------------------------------------


def save_schreiben_feedback(student_code: str, feedback: str, letter: str) -> None:
    """Persist the most recent AI feedback and original letter."""

    if not student_code:
        st.warning("No student code provided; feedback not saved.")
        return
    if db is None:
        st.warning("Firestore not initialized; feedback not saved.")
        return

    doc_ref = db.collection("schreiben_feedback").document(student_code)
    doc_ref.set(
        {
            "student_code": student_code,
            "feedback": feedback,
            "letter": letter,
            "date": firestore.SERVER_TIMESTAMP,
        }
    )


def load_schreiben_feedback(student_code: str) -> Tuple[str, str]:
    """Retrieve any saved AI feedback and the corresponding letter."""

    if not student_code:
        st.warning("No student code provided; feedback not loaded.")
        return "", ""
    if db is None:
        st.warning("Firestore not initialized; feedback not loaded.")
        return "", ""

    doc = db.collection("schreiben_feedback").document(student_code).get()
    if doc.exists:
        data = doc.to_dict() or {}
        return data.get("feedback", ""), data.get("letter", "")
    return "", ""


def delete_schreiben_feedback(student_code: str) -> None:
    """Remove saved feedback for a student."""

    if not student_code:
        st.warning("No student code provided; feedback not cleared.")
        return
    if db is None:
        st.warning("Firestore not initialized; feedback not cleared.")
        return
    db.collection("schreiben_feedback").document(student_code).delete()


# ---------------------------------------------------------------------------
# Letter Coach usage tracking
# ---------------------------------------------------------------------------


def get_letter_coach_usage(student_code: str) -> int:
    if not student_code:
        st.warning("No student code provided; usage assumed 0.")
        return 0
    if db is None:
        st.warning("Firestore not initialized; usage assumed 0.")
        return 0

    today = str(date.today())
    doc = db.collection("letter_coach_usage").document(
        f"{student_code}_{today}"
    ).get()
    return doc.to_dict().get("count", 0) if doc.exists else 0


def inc_letter_coach_usage(student_code: str) -> None:
    if not student_code:
        st.warning("No student code provided; usage assumed 0.")
        return
    if db is None:
        st.warning("Firestore not initialized; usage assumed 0.")
        return

    today = str(date.today())
    doc_ref = db.collection("letter_coach_usage").document(
        f"{student_code}_{today}"
    )
    try:
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({"count": firestore.Increment(1)})
        else:
            doc_ref.set({"student_code": student_code, "date": today, "count": 1})
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to increment Letter Coach usage: {exc}")


__all__ = [
    "update_schreiben_stats",
    "get_schreiben_stats",
    "save_submission",
    "save_schreiben_feedback",
    "load_schreiben_feedback",
    "delete_schreiben_feedback",
    "get_letter_coach_usage",
    "inc_letter_coach_usage",
]
