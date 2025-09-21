"""Custom chat helpers used by the Falowen Streamlit experience."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone as _timezone
import time
from typing import Callable, List, Optional

import logging

import streamlit as st

from src.draft_management import _draft_state_keys, autosave_maybe, save_now

TURN_LIMIT = 6
CUSTOM_CHAT_GREETING = "Hallo! 👋 What would you like to talk about? Give me details of what you want so I can understand."

_summary_client = None


def set_summary_client(client) -> None:
    """Configure the OpenAI client used for chat summaries."""

    global _summary_client
    _summary_client = client


@dataclass
class CustomChatResult:
    user_input: str
    save_clicked: bool
    chat_locked: bool
    use_chat_input: bool
    messages: List[dict]


def build_custom_chat_prompt(level: str, student_code: Optional[str] = None) -> str:
    if student_code is None:
        student_code = st.session_state.get("student_code", "")
    if level == "C1":
        return (
            "You are supportive German C1 Teacher. Speak both English and German. "
            "Ask one question at a time. Suggest useful starters, check C1 level. "
            "After correction, proceed to the next question using 'your next recommended question'. "
            "Stay on one topic; after 5 strong questions, give performance, score, and suggestions."
        )
    if level in ["A1", "A2", "B1", "B2"]:
        correction_lang = "in English" if level in ["A1", "A2"] else "half in English and half in German"
        rec_url = (
            "https://script.google.com/macros/s/AKfycbzMIhHuWKqM2ODaOCgtS7uZCikiZJRBhpqv2p6OyBmK1yAVba8HlmVC1zgTcGWSTfrsHA/exec"
            f"?code={student_code}"
        )
        return (
            "You are Herr Felix, a supportive and innovative German teacher. "
            "Start by congratulating the student in English for their chosen topic and outline the session: focus on confident speaking, vocabulary growth, and question practice across six turns leading to a short presentation. "
            "Encourage consistent study habits, remind them they can always ask for translations, and share one quick tip for building ideas if they feel stuck. "
            "If their input is a letter task, direct them to use the Schreiben tab ideas generator instead. "
            "Promise that after six answers you will build a 60-word presentation from their own words and share an audio-recording link in German. "
            "Choose three useful keywords for the topic and, for each keyword, ask up to two creative follow-up questions in German only, one at a time, and base the follow-up plan on the student's previous response. "
            "After every answer, deliver feedback in English, add one motivating suggestion in German, clearly explain any difficult words (A1–B2 level), and gently reinforce the teaching focus. "
            "If the student asks three grammar questions consecutively without attempting answers, pause the grammar chat politely and guide them back to their course book before continuing. "
            "After reaching six total questions, give final feedback in English and give them the presentation from their own words in German covering strengths, mistakes, and how to improve, summarise next steps in German, provide idea-building encouragement, and then share the recording link: "
            f"Always let them know how many question left for you to give them their presentation so they dont feel lost. "
            f"[Record your audio here]({rec_url}). Include the promised 60-word presentation composed from their own words in German and end with a motivational message wishing them good luck. "
            f"All feedback and corrections should be {correction_lang}. Keep it motivating and friendly throughout."
        )
    return ""


def generate_summary(messages: List[str]) -> str:
    """Use the configured OpenAI client to summarise custom chat answers."""

    if not messages:
        return ""
    prompt = "Summarize the following student responses into about 60 words suitable for a presentation."
    try:
        if _summary_client is None:
            raise RuntimeError("summary client not configured")
        resp = _summary_client.chat.completions.create(  # type: ignore[union-attr]
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "\n\n".join(messages)},
            ],
            temperature=0.7,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # pragma: no cover - network failures surfaced to logs
        logging.exception("Summary generation error: %s", exc)
        return ""


def increment_turn_count_and_maybe_close(is_exam: bool, *, summary_builder: Optional[Callable[[List[str]], str]] = None) -> bool:
    if is_exam:
        st.session_state["falowen_chat_closed"] = False
        st.session_state.pop("falowen_summary_emitted", None)
        return False

    st.session_state["falowen_chat_closed"] = False

    st.session_state["falowen_turn_count"] = st.session_state.get("falowen_turn_count", 0) + 1
    if st.session_state["falowen_turn_count"] < TURN_LIMIT:
        st.session_state["falowen_summary_emitted"] = False
        return False

    if st.session_state.get("falowen_summary_emitted"):
        return False

    builder = summary_builder or generate_summary
    user_msgs = [
        m.get("content", "")
        for m in st.session_state.get("falowen_messages", [])
        if m.get("role") == "user"
    ]
    summary = builder(user_msgs)
    messages = st.session_state.setdefault("falowen_messages", [])
    if not messages or messages[-1].get("role") != "assistant" or messages[-1].get("content") != summary:
        messages.append({"role": "assistant", "content": summary})
    st.session_state["falowen_summary_emitted"] = True
    return True


def render_custom_chat_input(
    *,
    draft_key: str,
    conv_key: str,
    student_code: str,
    widget_key: Callable[[str], str],
    render_umlaut_pad: Callable[[str, str, bool], None],
) -> CustomChatResult:
    """Render the non-exam chat input area and return interaction metadata."""

    use_chat_input = bool(st.session_state.get("falowen_use_chat_input"))
    chat_locked = False

    user_input_ci: Optional[str] = None
    user_input_btn = ""
    save_clicked = False

    if use_chat_input:
        user_input_ci = None if chat_locked else st.chat_input("Type your message…")
    else:
        col_in, col_btn = st.columns([8, 1])
        if st.session_state.pop("falowen_clear_draft", False):
            st.session_state[draft_key] = ""
            autosave_maybe(
                student_code,
                draft_key,
                st.session_state[draft_key],
                min_secs=0.0,
                min_delta=0,
                locked=chat_locked,
            )
            last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(
                draft_key
            )
            st.session_state[last_val_key] = st.session_state[draft_key]
            st.session_state[last_ts_key] = time.time()
            st.session_state[saved_flag_key] = True
            st.session_state[saved_at_key] = datetime.now(_timezone.utc)
        with col_in:
            st.text_area(
                "Type your answer...",
                key=draft_key,
                on_change=save_now,
                args=(draft_key, student_code),
                disabled=chat_locked,
            )
            render_umlaut_pad(draft_key, context=f"falowen_chat_{conv_key}", disabled=chat_locked)
            autosave_maybe(
                student_code,
                draft_key,
                st.session_state.get(draft_key, ""),
                min_secs=2.0,
                min_delta=12,
                locked=chat_locked,
            )
        with col_btn:
            send_clicked = st.button(
                "Send",
                key=widget_key("chat_send"),
                type="primary",
                disabled=chat_locked,
            )
        save_clicked = st.button(
            "Save draft",
            key=widget_key("chat_save_draft"),
            disabled=chat_locked,
            use_container_width=True,
        )
        user_input_btn = (
            st.session_state.get(draft_key, "").strip() if send_clicked and not chat_locked else ""
        )

    user_input = (user_input_ci or "").strip() if use_chat_input else user_input_btn

    return CustomChatResult(
        user_input=user_input,
        save_clicked=save_clicked,
        chat_locked=chat_locked,
        use_chat_input=use_chat_input,
        messages=list(st.session_state.get("falowen_messages", [])),
    )


__all__ = [
    "CustomChatResult",
    "CUSTOM_CHAT_GREETING",
    "TURN_LIMIT",
    "build_custom_chat_prompt",
    "generate_summary",
    "increment_turn_count_and_maybe_close",
    "render_custom_chat_input",
    "set_summary_client",
]
