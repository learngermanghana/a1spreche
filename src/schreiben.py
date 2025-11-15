"""Helpers for Schreiben statistics, feedback, and usage tracking.

These utilities were previously defined inside ``a1sprechen.py`` but have been
extracted into their own module for easier reuse and testing.
"""

from __future__ import annotations

import logging
import hashlib
from datetime import datetime, date
from typing import Optional, Tuple, Dict, Any

import re
import pandas as pd

import streamlit as st
from google.api_core.exceptions import GoogleAPICallError
from google.cloud.firestore_v1 import FieldFilter
from firebase_admin import firestore

try:  # Firestore may be unavailable in tests
    from falowen.sessions import get_db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - handle missing Firestore gracefully
    def get_db():  # type: ignore
        return None

db = None  # type: ignore


def _get_db():
    return db if db is not None else get_db()


# ---------------------------------------------------------------------------
# Feedback highlighting
# ---------------------------------------------------------------------------

highlight_words = ["correct", "should", "mistake", "improve", "tip"]


def highlight_feedback(text: str) -> str:
    """Return HTML with common feedback tags highlighted."""

    # Highlight ``[correct]`` spans in green
    text = re.sub(
        r"\[correct\](.+?)\[/correct\]",
        (
            "<span style='background-color:#d4edda;color:#155724;"
            "border-radius:4px;padding:2px 6px;margin:0 2px;font-weight:600;'>"
            r"\1</span>"
        ),
        text,
        flags=re.DOTALL,
    )

    # Highlight ``[wrong]`` spans in red with strikethrough
    text = re.sub(
        r"\[wrong\](.+?)\[/wrong\]",
        (
            "<span style='background-color:#f8d7da;color:#721c24;"
            "text-decoration:line-through;border-radius:4px;padding:2px 6px;"
            "margin:0 2px;font-weight:600;'>" r"\1</span>"
        ),
        text,
        flags=re.DOTALL,
    )

    # Highlight common keywords
    for word in highlight_words:
        text = re.sub(
            rf"\b({word})\b",
            r"<span style='background-color:#fff3cd;padding:0 4px;"
            "border-radius:4px;'>\1</span>",
            text,
            flags=re.IGNORECASE,
        )

    return text


# ---------------------------------------------------------------------------
# Usage tracking for Mark My Letter
# ---------------------------------------------------------------------------

def get_schreiben_usage(student_code: str) -> int:
    """Return today's Mark My Letter usage count for ``student_code``."""

    if not student_code:
        st.warning("No student code provided; usage unavailable.")
        return 0
    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; usage unavailable.")
        return 0
    today = str(date.today())
    doc = db.collection("schreiben_usage").document(f"{student_code}_{today}").get()
    return doc.to_dict().get("count", 0) if doc.exists else 0


def inc_schreiben_usage(student_code: str) -> None:
    """Increment today's Mark My Letter usage for ``student_code``."""

    if not student_code:
        st.warning("No student code provided; cannot increment usage.")
        return
    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; cannot increment usage.")
        return
    today = str(date.today())
    doc_ref = db.collection("schreiben_usage").document(f"{student_code}_{today}")
    try:
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({"count": firestore.Increment(1)})
        else:
            doc_ref.set({"student_code": student_code, "date": today, "count": 1})
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to increment Schreiben usage: {exc}")


# ---------------------------------------------------------------------------
# Letter Coach progress helpers
# ---------------------------------------------------------------------------

def save_letter_coach_progress(student_code: str, level: str, prompt: str, chat):
    """Persist Letter Coach progress for a student."""

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; progress not saved.")
        return
    try:
        db.collection("letter_coach_progress").document(student_code).set(
            {
                "student_code": student_code,
                "level": level,
                "prompt": prompt,
                "chat": chat,
                "date": firestore.SERVER_TIMESTAMP,
            }
        )
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to save Letter Coach progress: {exc}")


def load_letter_coach_progress(student_code: str):
    """Load Letter Coach progress for ``student_code``."""

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; cannot load progress.")
        return "", []
    doc = db.collection("letter_coach_progress").document(student_code).get()
    if doc.exists:
        data = doc.to_dict()
        return data.get("prompt", ""), data.get("chat", [])
    return "", []


def save_letter_coach_draft(
    student_code: str,
    prompt_draft: str,
    chat_draft: str,
) -> None:
    """Persist the in-progress Letter Coach drafts for a student."""

    if not student_code:
        st.warning("No student code provided; draft not saved.")
        return

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; draft not saved.")
        return

    doc_ref = db.collection("letter_coach_drafts").document(student_code)
    payload = {
        "student_code": student_code,
        "prompt_draft": prompt_draft or "",
        "chat_draft": chat_draft or "",
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    try:
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.set(payload, merge=True)
        else:
            payload["created_at"] = firestore.SERVER_TIMESTAMP
            doc_ref.set(payload)
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to save Letter Coach draft: {exc}")


def load_letter_coach_draft(student_code: str):
    """Load in-progress Letter Coach drafts for ``student_code``."""

    if not student_code:
        st.warning("No student code provided; cannot load drafts.")
        return "", "", None, None

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; cannot load drafts.")
        return "", "", None, None

    doc = db.collection("letter_coach_drafts").document(student_code).get()
    if doc.exists:
        data = doc.to_dict() or {}
        prompt_draft = data.get("prompt_draft", "") or ""
        chat_draft = data.get("chat_draft", "") or ""
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        return prompt_draft, chat_draft, created_at, updated_at
    return "", "", None, None


def clear_letter_coach_draft(student_code: str) -> None:
    """Clear any saved in-progress Letter Coach drafts for ``student_code``."""

    if not student_code:
        st.warning("No student code provided; draft not cleared.")
        return

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; draft not cleared.")
        return

    try:
        db.collection("letter_coach_drafts").document(student_code).set(
            {
                "student_code": student_code,
                "prompt_draft": "",
                "chat_draft": "",
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to clear Letter Coach draft: {exc}")


# ---------------------------------------------------------------------------
# Level detection via Google Sheet
# ---------------------------------------------------------------------------

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/12NXf5FeVHr7JJT47mRHh7Jp-"
    "TC1yhPS7ZG6nzZVTt1U/export?format=csv"
)


@st.cache_data(ttl=300)
def load_sheet():  # pragma: no cover - caching behaviour not tested
    return pd.read_csv(SHEET_URL)


def get_level_from_code(student_code: str) -> str:
    """Look up a student's level from the shared Google Sheet."""

    df = load_sheet()
    student_code = str(student_code).strip().lower()
    if "StudentCode" not in df.columns:
        df.columns = [c.strip() for c in df.columns]
    if "StudentCode" in df.columns:
        matches = df[df["StudentCode"].astype(str).str.strip().str.lower() == student_code]
        if not matches.empty:
            level = matches.iloc[0]["Level"]
            return str(level).strip().upper() if pd.notna(level) else "A1"
    return "A1"
# ---------------------------------------------------------------------------
# Schreiben stats helpers
# ---------------------------------------------------------------------------


def update_schreiben_stats(student_code: str) -> None:
    """Recalculate stats for a student after each submission."""

    if not student_code:
        st.warning("No student code provided; skipping stats update.")
        return
    db = _get_db()
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
    db = _get_db()
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

def save_submission(
    student_code: str,
    score: int,
    passed: bool,
    timestamp: Optional[datetime],
    level: str,
    letter: str,
) -> None:
    """Persist a Schreiben submission in Firestore.

    Parameters
    ----------
    student_code:
        Unique identifier for the student making the submission.
    score:
        Score awarded for the submission.
    passed:
        Whether the submission is marked as passed.
    timestamp:
        Optional ``datetime`` of the submission. If ``None`` the Firestore
        server timestamp is used instead.
    level:
        CEFR level of the student at the time of submission.
    letter:
        The submitted letter text.
    """

    if not student_code:
        st.warning("No student code provided; submission not saved.")
        return
    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; submission not saved.")
        return

    db.collection("schreiben_submissions").add(
        {
            "student_code": student_code,
            "score": score,
            "passed": passed,
            "date": timestamp or firestore.SERVER_TIMESTAMP,
            "level": level,
            "letter": letter,
        }
    )


# ---------------------------------------------------------------------------
# Schreiben feedback helpers
# ---------------------------------------------------------------------------


def save_schreiben_feedback(student_code: str, feedback: str, letter: str) -> None:
    """Persist the most recent AI feedback and original letter."""

    if not student_code:
        st.warning("No student code provided; feedback not saved.")
        return
    db = _get_db()
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
    db = _get_db()
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
    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; feedback not cleared.")
        return
    db.collection("schreiben_feedback").document(student_code).delete()


def vocab_practice_word_key(level: str, german: str, english: str) -> str:
    """Return a stable hash for a vocab entry."""

    base = f"{level}|{german}|{english}".strip().lower()
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def load_vocab_practice_progress(student_code: str) -> Dict[str, Dict[str, Any]]:
    """Load per-word vocab practice progress for a student."""

    if not student_code:
        st.warning("No student code provided; vocab progress unavailable.")
        return {}

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; vocab progress unavailable.")
        return {}

    doc = db.collection("schreiben_vocab_progress").document(student_code).get()
    if not doc.exists:
        return {}
    data = doc.to_dict() or {}
    return data.get("entries", {}) or {}


def set_vocab_practice_status(
    student_code: str,
    *,
    level: str,
    german: str,
    english: str,
    practiced: bool,
) -> None:
    """Persist whether a vocab entry has been practiced by the student."""

    if not student_code:
        st.warning("No student code provided; vocab progress not saved.")
        return

    db = _get_db()
    if db is None:
        st.warning("Firestore not initialized; vocab progress not saved.")
        return

    word_key = vocab_practice_word_key(level, german, english)
    doc_ref = db.collection("schreiben_vocab_progress").document(student_code)
    payload = {
        "student_code": student_code,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "entries": {
            word_key: {
                "level": level,
                "german": german,
                "english": english,
                "practiced": practiced,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        },
    }

    try:
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.set(payload, merge=True)
        else:
            payload["created_at"] = firestore.SERVER_TIMESTAMP
            doc_ref.set(payload)
    except Exception as exc:  # pragma: no cover - network failure
        st.error(f"Failed to update vocab progress: {exc}")


__all__ = [
    "update_schreiben_stats",
    "get_schreiben_stats",
    "save_submission",
    "save_schreiben_feedback",
    "load_schreiben_feedback",
    "delete_schreiben_feedback",
    "save_letter_coach_progress",
    "load_letter_coach_progress",
    "save_letter_coach_draft",
    "load_letter_coach_draft",
    "clear_letter_coach_draft",
    "vocab_practice_word_key",
    "load_vocab_practice_progress",
    "set_vocab_practice_status",
]
