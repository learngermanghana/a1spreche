"""Top-level orchestrator for the Vocab Trainer tab."""
from __future__ import annotations

import streamlit as st

from src.sentence_builder import render_sentence_builder
from src.stats import get_student_level
from src.vocab.dictionary import render_vocab_dictionary
from src.vocab.practice import render_vocab_practice


def render_vocab_trainer_tab() -> None:
    """Render the Vocab Trainer tab with its nested sub-tabs."""

    student_code = st.session_state.get("student_code", "") or ""
    if not student_code:
        st.error("Student code is required to access the vocab trainer.")
        st.stop()

    student_level_locked = (
        get_student_level(student_code, default=None)
        or st.session_state.get("student_level")
        or "A1"
    )

    st.markdown(
        """
        <div style="
            padding:8px 12px; background:#6f42c1; color:#fff;
            border-radius:6px; text-align:center; margin-bottom:8px;
            font-size:1.3rem;">
        📚 Vocab Trainer
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Practicing Level:** `{student_level_locked}` (from your profile)"
    )
    st.caption(
        "Your level is loaded automatically from the school list. Ask your tutor if this looks wrong."
    )
    st.divider()

    subtab = st.radio(
        "Choose practice:",
        ["Sentence Builder", "Vocab Practice", "All Vocabs"],
        horizontal=True,
        key="vocab_practice_subtab",
    )

    if subtab == "Sentence Builder":
        render_sentence_builder(student_code, student_level_locked)
    elif subtab == "Vocab Practice":
        render_vocab_practice(student_code, student_level_locked)
    else:
        render_vocab_dictionary(student_level_locked)
