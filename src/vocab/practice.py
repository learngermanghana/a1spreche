"""Vocab practice sub-tab rendering."""
from __future__ import annotations

import importlib
import random
from typing import TYPE_CHECKING, Tuple
from uuid import uuid4

import streamlit as st

from src.services.vocab import VOCAB_LISTS, get_audio_url
from src.stats import save_vocab_attempt, vocab_attempt_exists
from src.stats_ui import render_vocab_stats
from src.utils.toasts import refresh_with_toast

if TYPE_CHECKING:  # pragma: no cover - runtime import to avoid circular dependency
    from typing import Callable

    from a1sprechen import _dict_tts_bytes_de as DictTtsFn
    from a1sprechen import is_correct_answer as IsCorrectAnswerFn
    from a1sprechen import render_message as RenderMessageFn
    from a1sprechen import render_umlaut_pad as RenderUmlautPadFn


_HELPERS: Tuple[
    "IsCorrectAnswerFn",
    "RenderMessageFn",
    "DictTtsFn",
    "RenderUmlautPadFn",
] | None = None


def _get_app_helpers() -> Tuple[
    "IsCorrectAnswerFn",
    "RenderMessageFn",
    "DictTtsFn",
    "RenderUmlautPadFn",
]:
    """Lazy import helpers from :mod:`a1sprechen` to avoid circular imports."""

    global _HELPERS
    if _HELPERS is None:
        app_module = importlib.import_module("a1sprechen")
        _HELPERS = (
            getattr(app_module, "is_correct_answer"),
            getattr(app_module, "render_message"),
            getattr(app_module, "_dict_tts_bytes_de"),
            getattr(app_module, "render_umlaut_pad"),
        )
    return _HELPERS


def render_vocab_practice(student_code: str, level: str) -> None:
    """Render the Vocab Practice experience for *student_code* at *level*."""

    (
        is_correct_answer,
        render_message,
        dict_tts_bytes,
        render_umlaut_pad,
    ) = _get_app_helpers()

    defaults = {
        "vt_history": [],
        "vt_list": [],
        "vt_index": 0,
        "vt_score": 0,
        "vt_total": None,
        "vt_saved": False,
        "vt_session_id": None,
        "vt_mode": "Only new words",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    stats = render_vocab_stats(student_code)

    items = VOCAB_LISTS.get(level, [])
    completed = set(stats["completed_words"])
    not_done = [pair for pair in items if pair[0] not in completed]
    st.info(f"{len(not_done)} words NOT yet done at {level}.")

    if st.button("🔁 Start New Practice", key="vt_reset"):
        for key in defaults:
            st.session_state[key] = defaults[key]
        refresh_with_toast()

    if st.session_state.vt_total is None:
        with st.form("vt_setup"):
            st.subheader("Daily Practice Setup")
            mode = st.radio(
                "Select words:",
                ["Only new words", "All words"],
                horizontal=True,
                key="vt_mode",
            )
            session_vocab = (not_done if mode == "Only new words" else items).copy()
            max_count = len(session_vocab)
            if max_count == 0:
                st.success("🎉 All done! Switch to 'All words' to repeat.")
                st.stop()
            count = st.number_input(
                "How many today?",
                1,
                max_count,
                min(7, max_count),
                key="vt_count",
            )
            submitted = st.form_submit_button("Start")
        if submitted:
            random.shuffle(session_vocab)
            st.session_state.vt_list = session_vocab[:count]
            st.session_state.vt_total = count
            st.session_state.vt_index = 0
            st.session_state.vt_score = 0
            st.session_state.vt_history = [
                ("assistant", f"Hallo! Ich bin Herr Felix. Let's do {count} words!")
            ]
            st.session_state.vt_saved = False
            st.session_state.vt_session_id = str(uuid4())
            refresh_with_toast()
    else:
        st.markdown("### Daily Practice Setup")
        st.info(
            f"{st.session_state.vt_total} words · {st.session_state.get('vt_mode')}"
        )
        if st.button("Change goal", key="vt_change_goal"):
            st.session_state.vt_total = None
            refresh_with_toast()

    total = st.session_state.vt_total
    index = st.session_state.vt_index
    score = st.session_state.vt_score

    if st.session_state.vt_history:
        if isinstance(total, int) and total:
            remaining = total - index
            col_progress, col_score = st.columns(2)
            with col_progress:
                st.metric("Words", f"{index}/{total}", f"{remaining} left")
                st.progress(index / total)
            with col_score:
                st.metric("Score", score)

        st.markdown("### 🗨️ Practice Chat")
        for who, message in st.session_state.vt_history:
            render_message(who, message)

    if isinstance(total, int) and index < total:
        current = st.session_state.vt_list[index]
        word, answer = current[0], current[1]

        audio_url = get_audio_url(level, word)
        if audio_url:
            st.markdown(f"[⬇️ Download / Open MP3]({audio_url})")
        else:
            audio_bytes = dict_tts_bytes(word)
            if audio_bytes:
                st.download_button(
                    "⬇️ Download MP3",
                    data=audio_bytes,
                    file_name=f"{word}.mp3",
                    mime="audio/mpeg",
                    key=f"dl_{index}",
                )
            else:
                st.caption("Audio not available yet.")

        st.markdown(
            """
            <style>
            div[data-baseweb="input"] input {
                font-size: 18px !important;
                font-weight: 600 !important;
                color: black !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        input_key = f"vt_input_{index}"
        user_answer = st.text_input(
            f"{word} = ?",
            key=input_key,
            placeholder="Type your answer here...",
        )
        render_umlaut_pad(input_key, context=f"vocab_practice_{level}")
        if user_answer and st.button("Check", key=f"vt_check_{index}"):
            st.session_state.vt_history.append(("user", user_answer))
            if is_correct_answer(user_answer, answer):
                st.session_state.vt_score += 1
                feedback = f"✅ Correct! '{word}' = '{answer}'"
            else:
                feedback = f"❌ Nope. '{word}' = '{answer}'"
            st.session_state.vt_history.append(("assistant", feedback))
            st.session_state.vt_index += 1
            refresh_with_toast()

    if isinstance(total, int) and index >= total:
        score = st.session_state.vt_score
        words = [item[0] for item in (st.session_state.vt_list or [])]
        st.markdown(f"### 🏁 Done! You scored {score}/{total}.")
        if not st.session_state.get("vt_saved", False):
            if not st.session_state.get("vt_session_id"):
                st.session_state.vt_session_id = str(uuid4())
            if not vocab_attempt_exists(student_code, st.session_state.vt_session_id):
                save_vocab_attempt(
                    student_code=student_code,
                    level=level,
                    total=total,
                    correct=score,
                    practiced_words=words,
                    session_id=st.session_state.vt_session_id,
                )
            st.session_state.vt_saved = True
            refresh_with_toast()
        if st.button("Practice Again", key="vt_again"):
            for key in defaults:
                st.session_state[key] = defaults[key]
            refresh_with_toast()
