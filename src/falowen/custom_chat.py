"""Custom chat helpers used by the Falowen Streamlit experience (UPDATED).

Changes:
- Topic-locked, format-enforced prompt for A1–B2 (and a tighter C1 prompt).
- Guardrails to validate assistant output and auto-reformat if it drifts or violates format.
- Optional topic wiring + helpers for recording URL and session topic.

Integration notes:
- Store the user-selected topic into st.session_state via set_active_topic(topic).
- Build your system prompt by calling build_custom_chat_prompt(level, student_code, topic).
- After you receive the assistant's draft reply but before appending it to state, call
  enforce_format_or_regenerate(...) to ensure strict format and no early summaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone as _timezone
import re
import time
from typing import Callable, List, Optional

import logging

import streamlit as st

from src.draft_management import _draft_state_keys, autosave_maybe, save_now

# -----------------------------------------------------------------------------
# Constants & Globals
# -----------------------------------------------------------------------------

TURN_LIMIT = 6
CUSTOM_CHAT_GREETING = "Hallo! 👋 What would you like to talk about? Give me details of what you want so I can understand."

_summary_client = None
_chat_client = None  # optional separate client for chat completion reformatting


# -----------------------------------------------------------------------------
# Client set-up
# -----------------------------------------------------------------------------

def set_summary_client(client) -> None:
    """Configure the OpenAI client used for chat summaries."""
    global _summary_client
    _summary_client = client


def set_chat_client(client) -> None:
    """Configure the OpenAI client used for chat guardrail reformatting.

    If not set, enforce_format_or_regenerate will return the original text
    unchanged when a reformat would be required.
    """
    global _chat_client
    _chat_client = client


# -----------------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------------

@dataclass
class CustomChatResult:
    user_input: str
    save_clicked: bool
    chat_locked: bool
    use_chat_input: bool
    messages: List[dict]


# -----------------------------------------------------------------------------
# Helpers: topic + recording URL
# -----------------------------------------------------------------------------

def set_active_topic(topic: str) -> None:
    """Persist the session's active topic for the 6-turn flow."""
    st.session_state["falowen_topic"] = (topic or "").strip()


def get_active_topic(default: str = "kein Thema") -> str:
    return (st.session_state.get("falowen_topic", "").strip() or default)


def _recording_url(student_code: Optional[str]) -> str:
    if not student_code:
        student_code = st.session_state.get("student_code", "")
    return (
        "https://script.google.com/macros/s/AKfycbzMIhHuWKqM2ODaOCgtS7uZCikiZJRBhpqv2p6OyBmK1yAVba8HlmVC1zgTcGWSTfrsHA/exec"
        f"?code={student_code}"
    )


# -----------------------------------------------------------------------------
# Prompt builders (UPDATED)
# -----------------------------------------------------------------------------

def build_custom_chat_prompt(level: str, student_code: Optional[str] = None, topic: Optional[str] = None) -> str:
    """Build the strict system prompt for the current level.

    For A1–B2, this locks to ACTIVE_TOPIC, enforces a single-question turn format,
    bans survey/generalization language, and defines a final-turn template.
    """
    if student_code is None:
        student_code = st.session_state.get("student_code", "")
    if topic is None:
        topic = get_active_topic()

    if level == "C1":
        return (
            "You are a supportive German C1 teacher. Speak both English and German. "
            "Ask exactly ONE German question per turn. After each student reply, give concise corrections and feedback. "
            "Stay on ONE topic the student chose. Do NOT summarize or end until exactly 5 strong questions are complete. "
            "Then give performance, score, and suggestions."
        )

    if level in ["A1", "A2", "B1", "B2"]:
        correction_lang = "in English" if level in ["A1", "A2"] else "half in English and half in German"
        rec_url = _recording_url(student_code)

        return (
            "ROLE: You are Herr Felix, a supportive German teacher.\n"
            f"ACTIVE_TOPIC: {topic}\n"
            "SESSION PLAN: 6 turns (exactly). Ask ONE German question per turn, based on the student's previous answer. "
            "After the 6th answer ONLY, produce a ~60-word German mini-presentation assembled from the student's own words, "
            "final feedback in English, next steps in German, and the recording link.\n"
            "ABSOLUTE RULES:\n"
            "1) Stay on ACTIVE_TOPIC. Do NOT generalize to other students, surveys, participants, or groups. "
            "   Never write: 'In our survey', 'participants', or similar.\n"
            "2) Do NOT summarize or end early. If you are about to summarize before turn 6, instead ask the next question.\n"
            "3) Ask exactly ONE new German question per turn. No multiple questions in one turn.\n"
            "4) If the input is a letter task, briefly redirect to the Schreiben tab ideas generator and return to ACTIVE_TOPIC.\n"
            "5) Keywords: choose three useful keywords for the topic in the first turn only.\n"
            f"6) All feedback/corrections must be {correction_lang}. Keep tone friendly and motivating.\n"
            "7) Always show how many questions remain until the presentation.\n"
            "8) Use the EXACT OUTPUT FORMAT below. Do not add extra sections or prose outside these labels.\n\n"
            "OUTPUT FORMAT (every turn BEFORE the 6th summary):\n"
            "**IntroEN**: <one short line of encouragement or guidance in English>\n\n"
            "**Keywords**: <3 comma-separated words>  # only include on the FIRST turn; otherwise write '-'\n\n"
            "**Feedback**: <" + correction_lang + " corrections and clarity>\n\n"
            "**ExplainWords**: <brief meanings of any tricky words at this level>\n\n"
            "**MotivationDE**: <one short motivating sentence in German>\n\n"
            "**FrageDE**: <ONE German question, tailored to prior answer>\n\n"
            "**TurnsLeft**: <number from 5 down to 1>\n\n"
            "FINAL TURN (AFTER receiving the 6th student answer) — USE THIS FORMAT ONLY:\n"
            "**FinalFeedbackEN**: <overall feedback in English>\n\n"
            "**PraesentationDE**: <~60 words in German, composed from the student's own words>\n\n"
            "**NextStepsDE**: <brief, concrete next steps in German>\n\n"
            f"**RecordingLink**: [Record your audio here]({rec_url})\n\n"
            "**MotivationDE**: <one friendly closing line in German>\n"
        )
    return ""


# -----------------------------------------------------------------------------
# Summary generation (unchanged)
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Guardrails: format validation + auto-reformat
# -----------------------------------------------------------------------------

_SECTION_PATTERN = re.compile(
    r"^\*\*IntroEN\*\*:\s.+\n\n"
    r"\*\*Keywords\*\*:\s(.+|-)\n\n"
    r"\*\*Feedback\*\*:\s.+\n\n"
    r"\*\*ExplainWords\*\*:\s.*\n\n"
    r"\*\*MotivationDE\*\*:\s.+\n\n"
    r"\*\*FrageDE\*\*:\s.+\?\s*\n\n"
    r"\*\*TurnsLeft\*\*:\s[1-5]\s*$",
    re.DOTALL,
)



def is_valid_turn_text(text: str, *, is_final: bool, rec_url: str) -> bool:
    """Check if assistant text matches the required structure and constraints."""
    tl = text.lower()
    if is_final:
        required = ["FinalFeedbackEN:", "PraesentationDE:", "NextStepsDE:", "RecordingLink:", "MotivationDE:"]
        url_ok = (rec_url in text)
        return all(lbl in text for lbl in required) and url_ok and ("survey" not in tl) and ("participants" not in tl)
    return bool(_SECTION_PATTERN.match(text)) and ("survey" not in tl) and ("participants" not in tl)


def enforce_format_or_regenerate(
    draft_text: str,
    *,
    is_final: bool,
    system_prompt: str,
    dialog_messages: List[dict],
    rec_url: Optional[str] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3,
) -> str:
    """Ensure the assistant response follows the strict format.

    If invalid and a chat client is configured, request a reprint in the exact format
    without adding new content. If no client is configured, return the original text.
    """
    if rec_url is None:
        rec_url = _recording_url(st.session_state.get("student_code", ""))

    if is_valid_turn_text(draft_text, is_final=is_final, rec_url=rec_url):
        return draft_text

    if _chat_client is None:
        # No client to reformat—fallback to original (caller may decide to drop it)
        return draft_text

    try:
        resp = _chat_client.chat.completions.create(  # type: ignore[union-attr]
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                *dialog_messages,
                {
                    "role": "system",
                    "content": (
                        "Your last message violated the output format or rules (topic drift or early summary). "
                        "Reprint the SAME content strictly in the required OUTPUT FORMAT. "
                        "Do not add any new information. Do not mention this correction."
                    ),
                },
            ],
            temperature=temperature,
        )
        fixed = (resp.choices[0].message.content or "").strip()
        return fixed if is_valid_turn_text(fixed, is_final=is_final, rec_url=rec_url) else draft_text
    except Exception as exc:  # pragma: no cover
        logging.exception("Guardrail reformat error: %s", exc)
        return draft_text


# -----------------------------------------------------------------------------
# Turn counter & summary emission (unchanged behavior)
# -----------------------------------------------------------------------------

def increment_turn_count_and_maybe_close(
    is_exam: bool,
    *,
    summary_builder: Optional[Callable[[List[str]], str]] = None,
) -> bool:
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
        m.get("content", "") for m in st.session_state.get("falowen_messages", []) if m.get("role") == "user"
    ]
    summary = builder(user_msgs)
    messages = st.session_state.setdefault("falowen_messages", [])
    if not messages or messages[-1].get("role") != "assistant" or messages[-1].get("content") != summary:
        messages.append({"role": "assistant", "content": summary})
    st.session_state["falowen_summary_emitted"] = True
    return True


# -----------------------------------------------------------------------------
# UI: custom chat input (unchanged UI; includes autosave)
# -----------------------------------------------------------------------------

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
            last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(draft_key)
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


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

__all__ = [
    "CustomChatResult",
    "CUSTOM_CHAT_GREETING",
    "TURN_LIMIT",
    "build_custom_chat_prompt",
    "enforce_format_or_regenerate",
    "generate_summary",
    "increment_turn_count_and_maybe_close",
    "render_custom_chat_input",
    "set_active_topic",
    "get_active_topic",
    "set_summary_client",
    "set_chat_client",
]
