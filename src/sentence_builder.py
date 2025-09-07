"""Sentence Builder practice module.

Encapsulates the UI and state handling for the Sentence Builder feature that
was previously implemented directly inside ``a1sprechen.py``.
"""

import random
import re
from typing import Iterable

import streamlit as st

from src.config import SB_SESSION_TARGET
from src.sentence_bank import SENTENCE_BANK
from src.utils.toasts import refresh_with_toast


def _normalize_join(tokens: Iterable[str]) -> str:
    """Join tokens into a sentence with minimal spacing quirks."""
    sentence = " ".join(tokens)
    # remove spaces before punctuation
    return re.sub(r"\s+([,\.\!\?;:])", r"\1", sentence).strip()


# Optional imports; if unavailable (e.g. during tests) fall back to stubs.
try:  # pragma: no cover - best effort import
    from src.stats import get_sentence_progress  # type: ignore
except Exception:  # pragma: no cover - fallback stub
    def get_sentence_progress(student_code: str, level: str):
        total_items = len(SENTENCE_BANK.get(level, []))
        return 0, total_items

try:  # pragma: no cover - best effort import
    from src.stats import save_sentence_attempt  # type: ignore
except Exception:  # pragma: no cover - fallback stub
    def save_sentence_attempt(**kwargs):
        return None


def render_sentence_builder(student_code: str, student_level_locked: str) -> None:
    """Render the Sentence Builder practice interface."""
    student_level = student_level_locked
    st.info(
        f"✍️ You are practicing **Sentence Builder** at **{student_level}** (locked from your profile)."
    )

    with st.expander("✍️ Sentence Builder — Guide", expanded=False):
        st.caption("Click words in order; use Check/Next.")

    with st.expander("Progress", expanded=False):
        try:
            done_unique, total_items = get_sentence_progress(student_code, student_level)
        except Exception:
            total_items = len(SENTENCE_BANK.get(student_level, []))
            done_unique = 0
        pct = int((done_unique / total_items) * 100) if total_items else 0
        st.progress(pct)
        st.caption(
            f"Overall Progress: {done_unique} / {total_items} unique sentences correct ({pct}%)."
        )

    init_defaults = {
        "sb_round": 0,
        "sb_pool": None,
        "sb_pool_level": None,
        "sb_current": None,
        "sb_shuffled": [],
        "sb_selected_idx": [],
        "sb_score": 0,
        "sb_total": 0,
        "sb_feedback": "",
        "sb_correct": None,
    }
    for k, v in init_defaults.items():
        st.session_state.setdefault(k, v)

    if (st.session_state.sb_pool is None) or (
        st.session_state.sb_pool_level != student_level
    ):
        st.session_state.sb_pool_level = student_level
        st.session_state.sb_pool = (
            SENTENCE_BANK.get(student_level, SENTENCE_BANK.get("A1", [])).copy()
        )
        random.shuffle(st.session_state.sb_pool)
        st.session_state.sb_round = 0
        st.session_state.sb_score = 0
        st.session_state.sb_total = 0
        st.session_state.sb_feedback = ""
        st.session_state.sb_correct = None
        st.session_state.sb_current = None
        st.session_state.sb_selected_idx = []
        st.session_state.sb_shuffled = []

    def new_sentence() -> None:
        if not st.session_state.sb_pool:
            st.session_state.sb_pool = (
                SENTENCE_BANK.get(student_level, SENTENCE_BANK.get("A1", [])).copy()
            )
            random.shuffle(st.session_state.sb_pool)
        if st.session_state.sb_pool:
            st.session_state.sb_current = st.session_state.sb_pool.pop()
            words = st.session_state.sb_current.get("tokens", [])[:]
            random.shuffle(words)
            st.session_state.sb_shuffled = words
            st.session_state.sb_selected_idx = []
            st.session_state.sb_feedback = ""
            st.session_state.sb_correct = None
            st.session_state.sb_round += 1
        else:
            st.warning("No sentences available for this level.")

    if st.session_state.sb_current is None:
        new_sentence()

    target = SB_SESSION_TARGET
    cols = st.columns(2)
    with cols[0]:
        st.metric("Score (this session)", f"{st.session_state.sb_score}")
    with cols[1]:
        st.metric("Progress (this session)", f"{st.session_state.sb_total}/{target}")

    st.divider()

    cur = st.session_state.sb_current or {}
    prompt_en = cur.get("prompt_en", "")
    hint_en = cur.get("hint_en", "")
    grammar_tag = cur.get("grammar_tag", "")
    if prompt_en:
        st.markdown(
            f"""
            <div style="box-sizing:border-box; padding:12px 14px; margin:6px 0 14px 0;
                        background:#f0f9ff; border:1px solid #bae6fd; border-left:6px solid #0ea5e9;
                        border-radius:10px;">
              <div style="font-size:1.05rem;">
                🇬🇧 <b>Translate into German:</b> <span style="color:#0b4a6f">{prompt_en}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("💡 Need a nudge? (Hint)"):
            if hint_en:
                st.markdown(f"**Hint:** {hint_en}")
            if grammar_tag:
                st.caption(f"Grammar: {grammar_tag}")

    st.markdown("#### 🧩 Click the words in order")
    if st.session_state.sb_shuffled:
        word_cols = st.columns(min(6, len(st.session_state.sb_shuffled)) or 1)
        for i, w in enumerate(st.session_state.sb_shuffled):
            selected = i in st.session_state.sb_selected_idx
            btn_label = f"✅ {w}" if selected else w
            col = word_cols[i % len(word_cols)]
            with col:
                if st.button(
                    btn_label,
                    key=f"sb_word_{st.session_state.sb_round}_{i}",
                    disabled=selected,
                ):
                    st.session_state.sb_selected_idx.append(i)
                    refresh_with_toast()

    chosen_tokens = [
        st.session_state.sb_shuffled[i] for i in st.session_state.sb_selected_idx
    ]
    st.markdown("#### ✨ Your sentence")
    st.code(_normalize_join(chosen_tokens) if chosen_tokens else "—", language="text")

    a, b, c = st.columns(3)
    with a:
        if st.button("🧹 Clear"):
            st.session_state.sb_selected_idx = []
            st.session_state.sb_feedback = ""
            st.session_state.sb_correct = None
            refresh_with_toast()
    with b:
        if st.button("✅ Check"):
            target_sentence = st.session_state.sb_current.get("target_de", "").strip()
            chosen_sentence = _normalize_join(chosen_tokens).strip()
            correct = chosen_sentence.lower() == target_sentence.lower()
            st.session_state.sb_correct = correct
            st.session_state.sb_total += 1
            if correct:
                st.session_state.sb_score += 1
                st.session_state.sb_feedback = "✅ **Correct!** Great job!"
            else:
                tip = st.session_state.sb_current.get("hint_en", "")
                st.session_state.sb_feedback = (
                    f"❌ **Not quite.**\n\n**Correct:** {target_sentence}\n\n*Tip:* {tip}"
                )
            save_sentence_attempt(
                student_code=student_code,
                level=student_level,
                target_sentence=target_sentence,
                chosen_sentence=chosen_sentence,
                correct=correct,
                tip=st.session_state.sb_current.get("hint_en", ""),
            )
            refresh_with_toast()
    with c:
        next_disabled = st.session_state.sb_correct is None
        if st.button("➡️ Next", disabled=next_disabled):
            if st.session_state.sb_total >= target:
                st.success(
                    f"Session complete! Score: {st.session_state.sb_score}/{st.session_state.sb_total}"
                )
            new_sentence()
            refresh_with_toast()

    if st.session_state.sb_feedback:
        (st.success if st.session_state.sb_correct else st.info)(
            st.session_state.sb_feedback
        )


__all__ = ["render_sentence_builder"]
