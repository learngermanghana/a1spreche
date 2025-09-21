"""Core helpers orchestrating the Falowen chat experience.

This module bridges the navigation/state management helpers that power the
Streamlit flow with the chat specific utilities that live in
``src.falowen.custom_chat``.  The public API intentionally mirrors the
historical interface so callers can keep importing ``chat_core`` while the
heavy lifting lives in :mod:`src.falowen.custom_chat`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

import logging

import streamlit as st

from src.draft_management import _draft_state_keys
from src.firestore_utils import load_chat_draft_from_db
from src.utils.toasts import rerun_without_toast

from . import custom_chat as _custom_chat

# Re-export chat specific helpers so existing imports continue to function.
CustomChatResult = _custom_chat.CustomChatResult
CUSTOM_CHAT_GREETING = _custom_chat.CUSTOM_CHAT_GREETING
TURN_LIMIT = _custom_chat.TURN_LIMIT
build_custom_chat_prompt = _custom_chat.build_custom_chat_prompt
generate_summary = _custom_chat.generate_summary
increment_turn_count_and_maybe_close = (
    _custom_chat.increment_turn_count_and_maybe_close
)
render_custom_chat_input = _custom_chat.render_custom_chat_input
set_summary_client = _custom_chat.set_summary_client


@dataclass
class ChatSessionData:
    """Container describing the currently selected conversation."""

    conv_key: str
    draft_key: str
    doc_ref: Any
    doc_data: Dict[str, Any]
    fresh_chat: bool
    messages: Optional[List[dict]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def widget_key(name: str) -> str:
    """Return a deterministic widget key scoped to the active conversation."""

    prefix = st.session_state.get("falowen_loaded_key") or st.session_state.get(
        "falowen_conv_key", "falowen"
    )
    safe_prefix = prefix.replace(" ", "_")
    return f"{safe_prefix}_{name}"


def _conversation_namespace(mode: Optional[str], level: Optional[str], teil: Optional[str]) -> str:
    suffix = (teil or "custom").strip() or "custom"
    return f"{(mode or '').strip()}_{(level or '').strip()}_{suffix}".strip("_")


def _prefixed_keys(chats: Dict[str, List[dict]], namespace: str) -> List[str]:
    return [key for key in chats if key.startswith(namespace)]


def seed_initial_instruction(messages: List[dict]) -> None:
    """Ensure a conversation starts with the default assistant greeting."""

    if messages:
        return
    messages.append({"role": "assistant", "content": CUSTOM_CHAT_GREETING})
    st.session_state["falowen_messages"] = messages


def persist_messages(doc_ref: Any, conv_key: str, messages: Iterable[dict]) -> None:
    """Persist the latest conversation transcript to the backing store."""

    if doc_ref is None:
        return
    try:
        doc_ref.set({"chats": {conv_key: list(messages)}}, merge=True)
    except Exception as exc:  # pragma: no cover - Firestore failure paths
        logging.warning("Failed to persist chat for %s: %s", conv_key, exc)


def _load_chat_document(db: Any, student_code: str) -> tuple[Any, Dict[str, Any]]:
    if db is None or not student_code:
        return None, {}
    doc_ref = db.collection("falowen_chats").document(student_code)
    try:
        snapshot = doc_ref.get()
        if getattr(snapshot, "exists", False):
            return doc_ref, snapshot.to_dict() or {}
    except Exception as exc:  # pragma: no cover - Firestore failure paths
        logging.warning("Failed to load chats for %s: %s", student_code, exc)
    return doc_ref, {}


def _pick_existing_conv(
    *,
    namespace: str,
    chats: Dict[str, List[dict]],
    doc_data: Dict[str, Any],
    session_state_key: Optional[str],
) -> Optional[str]:
    if session_state_key and session_state_key in chats:
        return session_state_key

    current_conv = (doc_data.get("current_conv") or {}).get(namespace)
    if current_conv and current_conv in chats:
        return current_conv

    drafts = doc_data.get("drafts") or {}
    for draft_key in drafts:
        if draft_key.startswith(namespace) and draft_key in chats:
            return draft_key

    prefixed = _prefixed_keys(chats, namespace)
    if prefixed:
        return max(prefixed, key=lambda key: len(chats.get(key, [])))
    return None


def prepare_chat_session(
    *,
    db: Any,
    student_code: str,
    mode: Optional[str],
    level: Optional[str],
    teil: Optional[str],
) -> ChatSessionData:
    """Populate Streamlit state for the active conversation and return metadata."""

    namespace = _conversation_namespace(mode, level, teil)
    doc_ref, doc_data = _load_chat_document(db, student_code)
    chats = (doc_data.get("chats") or {})

    current = _pick_existing_conv(
        namespace=namespace,
        chats=chats,
        doc_data=doc_data,
        session_state_key=st.session_state.get("falowen_conv_key"),
    )

    fresh_chat = False
    if not current:
        current = f"{namespace}_{uuid4().hex[:8]}"
        chats = doc_data.setdefault("chats", {})
        chats[current] = []
        fresh_chat = True

    messages = list(chats.get(current, []))
    st.session_state["falowen_messages"] = messages
    st.session_state["falowen_conv_key"] = current
    st.session_state["falowen_loaded_key"] = current

    draft_key = f"falowen_chat_draft_{current}"
    st.session_state["falowen_chat_draft_key"] = draft_key
    draft_text = (
        load_chat_draft_from_db(student_code, current) if student_code else ""
    )
    st.session_state[draft_key] = draft_text

    if doc_ref is not None:
        try:
            doc_ref.set({"current_conv": {namespace: current}}, merge=True)
        except Exception as exc:  # pragma: no cover - Firestore failure paths
            logging.warning(
                "Failed to update current conversation for %s/%s: %s",
                student_code,
                namespace,
                exc,
            )

    return ChatSessionData(
        conv_key=current,
        draft_key=draft_key,
        doc_ref=doc_ref,
        doc_data=doc_data,
        fresh_chat=fresh_chat,
        messages=messages,
    )


def reset_falowen_chat_flow() -> None:
    """Reset chat specific state without clearing the level/mode selection."""

    st.session_state["falowen_turn_count"] = 0
    st.session_state["falowen_messages"] = []
    st.session_state["falowen_chat_closed"] = False
    st.session_state["custom_topic_intro_done"] = False
    st.session_state.pop("falowen_summary_emitted", None)


def back_step() -> None:
    """Return to the first wizard step and clear chat related state."""

    draft_key = st.session_state.pop("falowen_chat_draft_key", None)
    if draft_key:
        st.session_state.pop(draft_key, None)
        for extra in _draft_state_keys(draft_key):
            st.session_state.pop(extra, None)

    for key in [
        "falowen_mode",
        "falowen_teil",
        "falowen_exam_topic",
        "falowen_exam_keyword",
        "falowen_messages",
        "falowen_loaded_key",
        "falowen_conv_key",
        "custom_topic_intro_done",
        "falowen_turn_count",
        "falowen_chat_closed",
        "falowen_summary_emitted",
    ]:
        st.session_state.pop(key, None)

    st.session_state["falowen_stage"] = 1
    st.session_state["_falowen_loaded"] = False

    rerun_without_toast()


def render_chat_stage(
    *,
    client: Any,
    db: Any,
    highlight_words: Iterable[str],
    bubble_user: str,
    bubble_assistant: str,
    highlight_keywords,
    generate_chat_pdf,
    render_umlaut_pad,
) -> None:
    """Render the Streamlit UI for the chat stage."""

    del client, highlight_words, bubble_user, bubble_assistant, highlight_keywords
    del generate_chat_pdf

    session = prepare_chat_session(
        db=db,
        student_code=st.session_state.get("student_code", ""),
        mode=st.session_state.get("falowen_mode"),
        level=st.session_state.get("falowen_level"),
        teil=st.session_state.get("falowen_teil"),
    )

    namespace = _conversation_namespace(
        st.session_state.get("falowen_mode"),
        st.session_state.get("falowen_level"),
        st.session_state.get("falowen_teil"),
    )

    chats = (session.doc_data.get("chats") or {})
    options = sorted(_prefixed_keys(chats, namespace))
    if session.conv_key not in options:
        options.append(session.conv_key)

    selected_key = st.selectbox(
        "Previous chats",
        options,
        index=options.index(session.conv_key) if session.conv_key in options else 0,
        key=widget_key("chat_selector"),
    )

    if selected_key != session.conv_key:
        st.session_state["falowen_conv_key"] = selected_key
        st.session_state.pop("falowen_messages", None)
        st.session_state["falowen_clear_draft"] = True
        rerun_without_toast()
        return

    messages = st.session_state.setdefault("falowen_messages", session.messages or [])
    if session.fresh_chat:
        seed_initial_instruction(messages)
        persist_messages(session.doc_ref, session.conv_key, messages)

    render_custom_chat_input(
        draft_key=session.draft_key,
        conv_key=session.conv_key,
        student_code=st.session_state.get("student_code", ""),
        widget_key=widget_key,
        render_umlaut_pad=render_umlaut_pad,
    )


__all__ = [
    "ChatSessionData",
    "CustomChatResult",
    "CUSTOM_CHAT_GREETING",
    "TURN_LIMIT",
    "back_step",
    "build_custom_chat_prompt",
    "generate_summary",
    "increment_turn_count_and_maybe_close",
    "persist_messages",
    "prepare_chat_session",
    "render_chat_stage",
    "render_custom_chat_input",
    "reset_falowen_chat_flow",
    "seed_initial_instruction",
    "set_summary_client",
    "widget_key",
]
