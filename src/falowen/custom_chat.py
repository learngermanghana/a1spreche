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
            "You are a supportive German C1 teacher. Speak both English and German. "
            "Ask exactly one question at a time. Give targeted feedback. "
            "After correction, proceed with a clearly labeled 'Next recommended question'. "
            "Stay on one topic; after 5 strong questions, give performance, score, and suggestions. "
            "NEVER switch to surveys or third-person narration."
        )

    if level in ["A1", "A2", "B1", "B2"]:
        correction_lang = (
            "in English" if level in ["A1", "A2"] else "half in English and half in German"
        )
        rec_url = (
            "https://script.google.com/macros/s/AKfycbzMIhHuWKqM2ODaOCgtS7uZCikiZJRBhpqv2p6OyBmK1yAVba8HlmVC1zgTcGWSTfrsHA/exec"
            f"?code={student_code}"
        )
        return (
            "ROLE: You are Herr Felix, a supportive, motivating German teacher. "
            "INTERACTION RULES (hard constraints): "
            "1) Address the student directly (du/Sie); never mention other students, surveys, or groups. "
            "2) NO third-person summaries, NO meta commentary, NO surveys; never start with 'In our survey' or similar. "
            "3) Ask exactly ONE question in German per turn, based on the student's last answer. "
            "4) Do not generate the final presentation until AFTER six student answers. "
            "5) If the user asks three grammar questions consecutively without attempting answers, pause politely and direct them briefly to the course book, then continue. "
            "6) If the input is a letter task, direct them to the Schreiben tab ideas generator (briefly). "
            "7) Keep tone friendly and concise. "
            "SESSION FLOW: Start by congratulating them in English for their topic and outline the session (6 turns → short presentation). "
            "Share one quick tip for building ideas if stuck. Choose three useful keywords for the topic. "
            "For each keyword, ask up to two creative follow-ups over time (one per turn). "
            f"After every student answer: give feedback {correction_lang}, add one short motivating line in German, explain any difficult words (A1–B2), and remind how many questions remain. "
            "After exactly six total student answers: provide final feedback in English, then a 60-word German presentation composed from the student's own words (no third-person, no surveys), "
            "then summarise next steps in German, encourage them, and include the link below. "
            "OUTPUT FORMAT (strict): "
            "<response>"
            "<question_de>…exactly one German question ending with '?'…</question_de>"
            f"<feedback_{'en' if level in ['A1','A2'] else 'mix'}>…2–3 sentences…</feedback_{'en' if level in ['A1','A2'] else 'mix'}>"
            "<motivation_de>…one short German line…</motivation_de>"
            "<vocab_explain>• Wort – EN meaning; • Wort – EN meaning (max 3)</vocab_explain>"
            "<progress_de>Noch X Frage(n) bis zur Präsentation.</progress_de>"
            "</response> "
            "For the final turn (after 6 answers), replace <question_de> with <abschluss_de> containing encouragement and "
            f"the recording link: [Record your audio here]({rec_url}), and include <praesentation_de> with ~60 words built ONLY from the student's content."
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


# -------------------
# Turn counting fixes
# -------------------

def _count_user_answers() -> int:
    """Count only student/user messages with non-empty content."""
    msgs = st.session_state.get("falowen_messages", [])
    return sum(
        1
        for m in msgs
        if m.get("role") == "user" and (m.get("content") or "").strip()
    )


def increment_turn_count_and_maybe_close(
    is_exam: bool, *, summary_builder: Optional[Callable[[List[str]], str]] = None
) -> bool:
    """
    For non-exam chats, consider emitting a summary after exactly TURN_LIMIT user answers.
    Returns True if a summary message was appended this call.
    """
    if is_exam:
        st.session_state["falowen_chat_closed"] = False
        st.session_state.pop("falowen_summary_emitted", None)
        return False

    st.session_state["falowen_chat_closed"] = False

    # Derive count from messages to avoid drift
    answers = _count_user_answers()
    st.session_state["falowen_turn_count"] = answers

    if answers < TURN_LIMIT:
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
    if (
        not messages
        or messages[-1].get("role") != "assistant"
        or messages[-1].get("content") != summary
    ):
        messages.append({"role": "assistant", "content": summary})
    st.session_state["falowen_summary_emitted"] = True
    return True


# -------------------
# Output guardrails
# -------------------

BANNED_PHRASES = [
    "In our survey",
    "many students mentioned",
    "participants",
    "survey",
    "study shows",
    "students said",
]


def _violates_guardrails(s: str) -> bool:
    """Basic check for survey/third-person drift and required tag presence."""
    if not s:
        return True
    low = s.lower()
    if any(p.lower() in low for p in BANNED_PHRASES):
        return True

    # Allow the very first assistant greeting without tags
    if _count_user_answers() == 0:
        return False

    # After the first user reply, require one of the mandated tags
    needs_tags = any(
        tag in s for tag in ["<question_de>", "<abschluss_de>", "<praesentation_de>"]
    )
    if not needs_tags:
        return True

    return False


def _minimal_repair_stub() -> str:
    """Safe, well-formed fallback if we cannot repair via API."""
    remaining = max(0, TURN_LIMIT - _count_user_answers())
    return (
        "<response>"
        "<question_de>Was kaufst du normalerweise im Supermarkt?</question_de>"
        "<feedback_en>Thanks for your answer! Keep responses short and clear. I’ll ask one question at a time and give quick feedback.</feedback_en>"
        "<motivation_de>Weiter so! Du machst das gut.</motivation_de>"
        "<vocab_explain>• Einkaufsliste – shopping list; • Rabatt – discount</vocab_explain>"
        f"<progress_de>Noch {remaining} Frage(n) bis zur Präsentation.</progress_de>"
        "</response>"
    )


def enforce_output_format_or_repair(
    text: str,
    *,
    messages: Optional[List[dict]] = None,
    client=None,
    model: str = "gpt-4o-mini",
) -> str:
    """
    If output violates guardrails, attempt a one-shot repair via the provided client.
    Falls back to a minimal, valid message if no client is available or the repair fails.
    """
    if not _violates_guardrails(text):
        return text

    repair_msg = (
        "Your previous output violated constraints (survey/third-person or wrong format). "
        "Regenerate STRICTLY following the current system prompt and this OUTPUT FORMAT: "
        "<response><question_de>…?</question_de><feedback_*>…</feedback_*><motivation_de>…</motivation_de>"
        "<vocab_explain>• Wort – EN; • Wort – EN</vocab_explain>"
        "<progress_de>Noch X Frage(n) bis zur Präsentation.</progress_de></response> "
        "Exactly ONE German question. No surveys. No third-person."
    )

    if client is None or messages is None:
        return _minimal_repair_stub()

    try:
        repaired = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": repair_msg}, *messages],
            temperature=0.2,
        )
        candidate = (repaired.choices[0].message.content or "").strip()
        return candidate if not _violates_guardrails(candidate) else _minimal_repair_stub()
    except Exception as exc:  # pragma: no cover
        logging.exception("Repair generation error: %s", exc)
        return _minimal_repair_stub()


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
            render_umlaut_pad(
                draft_key, context=f"falowen_chat_{conv_key}", disabled=chat_locked
            )
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
            st.session_state.get(draft_key, "").strip()
            if send_clicked and not chat_locked
            else ""
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
    "enforce_output_format_or_repair",
]
