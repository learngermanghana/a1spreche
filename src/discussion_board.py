"""Utilities for handling the class discussion board.

This module was extracted from the monolithic ``a1sprechen.py`` to make the
discussion-board functionality easier to maintain and test.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

try:  # Firestore may be unavailable in tests
    from falowen.sessions import get_db  # pragma: no cover - runtime side effect
except Exception:  # pragma: no cover - handle missing Firestore gracefully
    def get_db():  # type: ignore
        return None


# ---------------------------------------------------------------------------
# Constants for discussion links/buttons
# ---------------------------------------------------------------------------

CLASS_DISCUSSION_LABEL = "Class Discussion & Notes"
CLASS_DISCUSSION_LINK_TMPL = "go_discussion_{chapter}"
CLASS_DISCUSSION_ANCHOR = "#classnotes"
CLASS_DISCUSSION_PROMPT = "Discussion for this class can be found at"
CLASS_DISCUSSION_REMINDER = (
    "Your recorded lecture, grammar book, and workbook are saved below. "
    "Class notes are additional and cover discussions from class."
)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def go_class_thread(topic: str, db: Optional[object] = None) -> None:
    """Navigate to the class discussion thread for the current user.

    Parameters
    ----------
    topic:
        Chapter or topic identifier used to filter the board posts.
    db:
        Optional Firestore client. When omitted the default database from
        ``falowen.sessions`` is used. Passing a fake implementation makes the
        function easy to unit test.
    """

    if db is None:
        db = get_db()

    if db is None:
        st.warning(
            "Class discussion database is currently unavailable. "
            "Please try again later."
        )
        st.session_state["class_discussion_warning"] = True
        return

    student_level = st.session_state.get("student_level", "A1")
    class_name = (
        str(st.session_state.get("student_row", {}).get("ClassName", ""))
        .strip()
    )

    board_base = (
        db.collection("class_board")
        .document(student_level)
        .collection("classes")
        .document(class_name)
        .collection("posts")
    )
    posts = [
        snap
        for snap in board_base.stream()
        if snap.to_dict().get("topic") == topic
        or snap.to_dict().get("chapter") == topic
    ]
    count = len(posts)

    st.session_state["coursebook_subtab"] = "🧑‍🏫 Classroom"
    st.session_state["classroom_page"] = "Class Notes & Q&A"
    st.session_state["q_search_count"] = count
    if count == 0:
        st.session_state["q_search"] = ""
        st.session_state["q_search_warning"] = True
    else:
        st.session_state["q_search"] = topic
    st.session_state["__scroll_to_classnotes"] = True

