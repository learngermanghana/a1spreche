"""UI and query parameter helpers for the Falowen app."""
from __future__ import annotations

import re
from datetime import datetime
from typing import List

import streamlit as st


def qp_get():
    return st.query_params


def qp_clear():
    st.query_params.clear()


def qp_clear_keys(*keys):
    for k in keys:
        try:
            del st.query_params[k]
        except KeyError:
            pass


FALOWEN_QP_KEYS = [
    "falowen_stage",
    "falowen_mode",
    "falowen_level",
    "falowen_teil",
]


def seed_falowen_state_from_qp() -> None:
    """Seed st.session_state from query parameters if available."""
    try:
        qp = st.query_params
        for key in FALOWEN_QP_KEYS:
            if key in st.session_state:
                continue
            val = qp.get(key)
            if isinstance(val, list):
                val = val[0]
            if val is None:
                continue
            if key == "falowen_stage":
                try:
                    st.session_state[key] = int(val)
                except ValueError:
                    pass
            else:
                st.session_state[key] = val
    except Exception:
        pass


def persist_falowen_state_to_qp() -> None:
    """Persist current falowen state to query parameters."""
    vals = {k: st.session_state.get(k) for k in FALOWEN_QP_KEYS}
    stage = vals.get("falowen_stage")
    if stage in (None, 1, 5) and not any(
        vals.get(k) for k in ["falowen_mode", "falowen_level", "falowen_teil"]
    ):
        qp_clear_keys(*FALOWEN_QP_KEYS)
        return

    for key, val in vals.items():
        if val in (None, ""):
            try:
                del st.query_params[key]
            except KeyError:
                pass
        else:
            st.query_params[key] = str(val)


@st.cache_data(ttl=3600)
def build_wa_message(name: str, code: str, level: str, day: int, chapter: str, answer: str) -> str:
    """Build a WhatsApp-friendly submission message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = (answer or "").strip()
    return (
        "Learn Language Education Academy – Assignment Submission\n"
        f"Name: {name}\n"
        f"Code: {code}\n"
        f"Level: {level}\n"
        f"Day: {day}\n"
        f"Chapter: {chapter}\n"
        f"Date: {timestamp}\n"
        f"Answer: {body if body else '[See attached file/photo]'}"
    )


def highlight_terms(text: str, terms: List[str]) -> str:
    """Wrap each term in <span> to highlight matches inside text."""
    if not text:
        return ""
    for term in terms:
        if not str(term).strip():
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        text = pattern.sub(
            f"<span style='background:yellow;border-radius:0.23em;'>{term}</span>", text
        )
    return text


def filter_matches(lesson: dict, terms: List[str]) -> bool:
    """True if any search term appears in key lesson fields."""
    searchable = (
        str(lesson.get("topic", "")).lower()
        + str(lesson.get("chapter", "")).lower()
        + str(lesson.get("goal", "")).lower()
        + str(lesson.get("instruction", "")).lower()
        + str(lesson.get("grammar_topic", "")).lower()
        + str(lesson.get("day", "")).lower()
    )
    return any(term in searchable for term in terms)
