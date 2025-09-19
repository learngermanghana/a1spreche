"""Custom chat helpers used by the Falowen Streamlit experience."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

import logging

import streamlit as st

from src.draft_management import autosave_maybe, save_now

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
            "1) Congratulate the student in English for the topic, explain how the session will go (teaching + questions, total questions, expected outcome). "
            "Encourage asking for translations when needed. "
            "2) If their input is a letter task, ask them to use the Schreiben tab ideas generator instead. "
            "Promise: after 6 answers, build a 60-word presentation from their own words and give them a link to record audio. "
            "Pick 3 useful keywords for the topic; for each keyword ask up to 2 creative questions in German only (one at a time). "
            "After each answer: give feedback in English and a suggestion in German; explain difficult words (A1–B2). "
            "If they ask 3 grammar questions in a row without trying answers, politely pause grammar and direct them to their course book first. "
            "After reaching 6 total questions, give final feedback (strengths/mistakes/how to improve) in English, then link to record audio: "
            f"[Record your audio here]({rec_url}). Provide a 60-word presentation from their own words. "
            f"All feedback and corrections should be {correction_lang}. Keep it motivating."
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
            save_now(draft_key, student_code)
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
