"""Utility functions for working with vocabulary statistics.

The functions here were previously embedded inside ``a1sprechen.py`` but have
been extracted so they can be imported independently and tested.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable, Optional

import os
import pandas as pd
import streamlit as st

try:  # Firestore access is optional in tests
    from falowen.sessions import db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - Firestore may be unavailable
    db = None  # type: ignore

# Maximum number of vocab practice attempts to retain per student
MAX_HISTORY = 100


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------


def _get_db():
    """Return the Firestore client if initialised, otherwise ``None``."""

    return db  # may be ``None``


# ---------------------------------------------------------------------------
# Roster loading helpers
# ---------------------------------------------------------------------------


DEFAULT_ROSTER_SHEET_ID = "12NXf5FeVHr7JJT47mRHh7Jp-TC1yhPS7ZG6nzZVTt1U"



@st.cache_data
def load_student_levels():
    """Load the roster with a ``Level`` column from a Google Sheet."""
    
    sheet_id = (
        st.secrets.get("ROSTER_SHEET_ID")
        or os.getenv("ROSTER_SHEET_ID")
        or DEFAULT_ROSTER_SHEET_ID
    )
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:  # pragma: no cover - network/streamlit issues
        st.warning(
            f"Could not load roster from {csv_url} ({e}). Using empty roster."
        )
        return pd.DataFrame({"student_code": [], "level": []})
    df.columns = [c.strip().lower() for c in df.columns]

    code_col_candidates = ["student_code", "studentcode", "code", "student id", "id"]
    level_col_candidates = ["level", "klasse", "stufe"]
    code_col = next((c for c in code_col_candidates if c in df.columns), None)
    level_col = next((c for c in level_col_candidates if c in df.columns), None)
    if code_col is None or level_col is None:
        st.error(
            f"Roster is missing required columns. Found: {list(df.columns)}; "
            f"need one of {code_col_candidates} and one of {level_col_candidates}."
        )
        df["__dummy_code__"] = "demo001"
        df["__dummy_level__"] = "A1"
        return df.rename(
            columns={"__dummy_code__": "student_code", "__dummy_level__": "level"}
        )

    df = df.rename(columns={code_col: "student_code", level_col: "level"})
    return df


def get_student_level(student_code: str, default: Optional[str] = None) -> Optional[str]:
    """Return the student's level from the roster.

    If the ``student_code`` cannot be found or the roster fails to load, this
    function returns ``default`` (which defaults to ``None``).
    """

    try:
        df = load_student_levels()
    except Exception as e:  # pragma: no cover - network/streamlit issues
        st.warning(f"Could not load level from roster ({e}). Using default {default}.")
        return default

    if "student_code" not in df.columns or "level" not in df.columns:
        return default

    sc = str(student_code).strip().lower()
    row = df[df["student_code"].astype(str).str.strip().str.lower() == sc]
    if not row.empty:
        return str(row.iloc[0]["level"]).upper().strip()

    return default
    
# ---------------------------------------------------------------------------
# Vocabulary practice statistics
# ---------------------------------------------------------------------------


def vocab_attempt_exists(student_code: str, session_id: str) -> bool:
    """Check if an attempt with this ``session_id`` already exists."""

    if not session_id:
        return False
    _db = _get_db()
    if _db is None:
        return False

    doc_ref = _db.collection("vocab_stats").document(student_code)
    try:
        doc = doc_ref.get()
    except Exception as e:  # pragma: no cover - firestore failure
        st.warning(f"Could not check existing attempt ({e}).")
        return False
    if not doc.exists:
        return False
    data = doc.to_dict() or {}
    history = data.get("history", [])
    return any(h.get("session_id") == session_id for h in history)


def save_vocab_attempt(
    student_code: str,
    level: str,
    total: int,
    correct: int,
    practiced_words: Iterable[str],
    session_id: Optional[str] = None,
) -> None:
    """Persist one vocab practice attempt to Firestore."""

    _db = _get_db()
    if _db is None:
        st.warning("Firestore not initialized; skipping stats save.")
        return

    from uuid import uuid4

    if not session_id:
        session_id = str(uuid4())

    if vocab_attempt_exists(student_code, session_id):
        return

    doc_ref = _db.collection("vocab_stats").document(student_code)
    try:
        doc = doc_ref.get()
    except Exception as e:  # pragma: no cover - firestore failure
        st.warning(f"Could not load existing stats ({e}); skipping save.")
        return
    data = doc.to_dict() if doc.exists else {}
    history = data.get("history", [])
    total_sessions = data.get("total_sessions", len(history))

    
    raw_total = int(total) if total is not None else 0
    if raw_total < 0:
        st.warning(f"Total {raw_total} is negative; clamping to 0.")
    total_int = max(raw_total, 0)

    raw_correct = int(correct) if correct is not None else 0
    if raw_correct < 0:
        st.warning(f"Correct {raw_correct} is negative; clamping to 0.")
    correct_int = max(raw_correct, 0)
    if correct_int > total_int:
        st.warning(
            f"Correct {correct_int} exceeds total {total_int}; clamping to total."
        )
        correct_int = total_int

    attempt = {
        "level": level,
        "total": total_int,
        "correct": correct_int,
        "practiced_words": list(practiced_words or []),
        "timestamp": datetime.now(tz=UTC).isoformat(timespec="minutes"),
        "session_id": session_id,
    }

    history.append(attempt)
    total_sessions += 1
    history = history[-MAX_HISTORY:]
    completed = {w for a in history for w in a.get("practiced_words", [])}

    try:
        doc_ref.set(
            {
                "history": history,
                "last_practiced": attempt["timestamp"],
                "completed_words": sorted(completed),
                "total_sessions": total_sessions,
            },
            merge=True,
        )
    except Exception as e:  # pragma: no cover - firestore failure
        st.warning(f"Could not save stats ({e}).")


def get_vocab_stats(student_code: str):
    """Load vocab practice stats from Firestore (or return defaults)."""

    _db = _get_db()
    if _db is None:
        return {
            "history": [],
            "last_practiced": None,
            "completed_words": [],
            "total_sessions": 0,
        }

    doc_ref = _db.collection("vocab_stats").document(student_code)
    try:
        doc = doc_ref.get()
    except Exception as e:  # pragma: no cover - firestore failure
        st.warning(f"Could not load stats ({e}); returning defaults.")
        return {
            "history": [],
            "last_practiced": None,
            "completed_words": [],
            "total_sessions": 0,
        }
    if doc.exists:
        data = doc.to_dict() or {}
        history = data.get("history", [])
        total_sessions = data.get("total_sessions")
        if total_sessions is None:
            total_sessions = len(history)
        data = doc.to_dict() or {}
        return {
            "history": history,
            "last_practiced": data.get("last_practiced"),
            "completed_words": data.get("completed_words", []),
            "total_sessions": total_sessions,
        }

    return {
        "history": [],
        "last_practiced": None,
        "completed_words": [],
        "total_sessions": 0,
    }
