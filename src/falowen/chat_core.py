"""Core helpers shared by Falowen's chat experiences."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone as _timezone
import hashlib
import time
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

import streamlit as st

from src.draft_management import _draft_state_keys, autosave_maybe, save_now
from src.firestore_utils import load_chat_draft_from_db
from src.utils.toasts import rerun_without_toast

from . import custom_chat, exams_mode


def widget_key(base: str, *, student_code: Optional[str] = None) -> str:
    """Stable widget key namespaced by student code."""

    sc = student_code or str(st.session_state.get("student_code", "anon"))
    digest = hashlib.md5(f"{base}|{sc}".encode()).hexdigest()[:8]
    return f"{base}_{digest}"


def reset_falowen_chat_flow(*, clear_messages: bool = True, clear_intro: bool = True) -> None:
    if clear_messages:
        st.session_state["falowen_messages"] = []
    if clear_intro:
        st.session_state["custom_topic_intro_done"] = False
    st.session_state["falowen_turn_count"] = 0
    st.session_state["falowen_chat_closed"] = False
    st.session_state.pop("falowen_summary_emitted", None)


def back_step() -> None:
    draft_key = st.session_state.get("falowen_chat_draft_key")
    for key in [
        "falowen_mode",
        "falowen_level",
        "falowen_teil",
        "falowen_exam_topic",
        "falowen_exam_keyword",
        "falowen_messages",
        "falowen_loaded_key",
        "falowen_conv_key",
        "falowen_chat_draft_key",
        "custom_topic_intro_done",
        "falowen_turn_count",
        "falowen_chat_closed",
        "falowen_summary_emitted",
    ]:
        st.session_state.pop(key, None)
    if draft_key:
        st.session_state.pop(draft_key, None)
        for extra in _draft_state_keys(draft_key):
            st.session_state.pop(extra, None)
    st.session_state["_falowen_loaded"] = False
    st.session_state["falowen_stage"] = 1
    rerun_without_toast()


@dataclass
class ChatSessionData:
    conv_key: str
    draft_key: str
    doc_ref: Any
    doc_data: Dict[str, Any]
    fresh_chat: bool


def prepare_chat_session(
    *,
    db,
    student_code: str,
    mode: str,
    level: str,
    teil: Optional[str],
) -> ChatSessionData:
    mode_level_teil = f"{mode}_{level}_{teil or 'custom'}"
    doc_ref = None
    doc_data: Dict[str, Any] = {}
    if db is not None:
        doc_ref = db.collection("falowen_chats").document(student_code)
        try:
            snap = doc_ref.get()
            doc_data = snap.to_dict() or {} if snap.exists else {}
        except Exception:
            doc_ref = None
            doc_data = {}

    conv_key = st.session_state.get("falowen_conv_key")
    fresh_chat = False
    if not conv_key or not str(conv_key).startswith(f"{mode_level_teil}_"):
        conv_key = (doc_data.get("current_conv", {}) or {}).get(mode_level_teil)
        if not conv_key or not str(conv_key).startswith(f"{mode_level_teil}_"):
            drafts = (doc_data.get("drafts", {}) or {})
            conv_key = next((k for k in drafts if str(k).startswith(f"{mode_level_teil}_")), None)
        if not conv_key:
            conv_key = f"{mode_level_teil}_{uuid4().hex[:8]}"
            fresh_chat = True
        if doc_ref is not None:
            try:
                doc_ref.set({"current_conv": {mode_level_teil: conv_key}}, merge=True)
            except Exception:
                pass
    st.session_state["falowen_conv_key"] = conv_key

    draft_key = widget_key("chat_draft", student_code=student_code)
    st.session_state["falowen_chat_draft_key"] = draft_key

    current_messages = st.session_state.get("falowen_messages", [])
    loaded_key = st.session_state.get("falowen_loaded_key")
    chats = (doc_data.get("chats", {}) or {})
    remote_messages = chats.get(conv_key)
    if loaded_key != conv_key:
        current_messages = []
        fresh_chat = True
    if isinstance(remote_messages, list):
        st.session_state["falowen_messages"] = remote_messages
    else:
        st.session_state["falowen_messages"] = current_messages

    if fresh_chat:
        reset_falowen_chat_flow(clear_messages=False, clear_intro=False)

    draft_text = ""
    try:
        draft_text = load_chat_draft_from_db(student_code, conv_key)
    except Exception:
        draft_text = ""
    st.session_state[draft_key] = draft_text
    last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(draft_key)
    st.session_state[last_val_key] = draft_text
    st.session_state[last_ts_key] = time.time()
    st.session_state[saved_flag_key] = True
    st.session_state[saved_at_key] = datetime.now(_timezone.utc)
    st.session_state["falowen_loaded_key"] = conv_key

    return ChatSessionData(
        conv_key=conv_key,
        draft_key=draft_key,
        doc_ref=doc_ref,
        doc_data=doc_data,
        fresh_chat=fresh_chat,
    )


def persist_messages(
    student_code: str,
    conv_key: str,
    messages: List[Dict[str, str]],
    *,
    db,
    doc_ref,
    doc_data: Dict[str, Any],
) -> None:
    if doc_ref is None:
        if db is None:
            return
        doc_ref = db.collection("falowen_chats").document(student_code)
        try:
            snap = doc_ref.get()
            doc_data = snap.to_dict() or {} if snap.exists else {}
        except Exception:
            return

    chats = dict((doc_data or {}).get("chats", {}))
    chats[conv_key] = messages
    try:
        doc_ref.set({"chats": chats}, merge=True)
    except Exception:
        pass


def seed_initial_instruction(
    instruction: str,
    *,
    student_code: str,
    conv_key: str,
    db,
    doc_ref,
    doc_data: Dict[str, Any],
) -> None:
    if st.session_state.get("falowen_messages"):
        return
    st.session_state["falowen_messages"] = [{"role": "assistant", "content": instruction}]
    persist_messages(
        student_code,
        conv_key,
        st.session_state["falowen_messages"],
        db=db,
        doc_ref=doc_ref,
        doc_data=doc_data,
    )


@dataclass
class ExamInputResult:
    user_input: str
    save_clicked: bool


def _render_exam_input_area(
    *,
    draft_key: str,
    conv_key: str,
    student_code: str,
    widget_key_fn: Callable[[str], str],
    render_umlaut_pad: Callable[[str, str, bool], None],
) -> ExamInputResult:
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
        )
        render_umlaut_pad(draft_key, context=f"falowen_chat_{conv_key}", disabled=False)
        autosave_maybe(
            student_code,
            draft_key,
            st.session_state.get(draft_key, ""),
            min_secs=2.0,
            min_delta=12,
        )
    with col_btn:
        send_clicked = st.button(
            "Send",
            key=widget_key_fn("chat_send"),
            type="primary",
        )
    save_clicked = st.button(
        "Save draft",
        key=widget_key_fn("chat_save_draft"),
        use_container_width=True,
    )
    user_input = st.session_state.get(draft_key, "").strip() if send_clicked else ""
    return ExamInputResult(user_input=user_input, save_clicked=save_clicked)


def _render_recorder_button(widget_key_fn: Callable[[str], str], student_code: str) -> None:
    recorder_base = (
        "https://script.google.com/macros/s/"
        "AKfycbzMIhHuWKqM2ODaOCgtS7uZCikiZJRBhpqv2p6OyBmK1yAVba8HlmVC1zgTcGWSTfrsHA/exec"
    )
    rec_url = f"{recorder_base}?code={student_code}"
    label = "\U0001F399\ufe0f Record your answer now (Sprechen Recorder)"
    fallback = (
        '<a href="{url}" target="_blank" rel="noopener noreferrer" '
        'style="display:block;text-align:center;padding:12px 16px;border-radius:10px;'
        'background:#2563eb;color:#fff;text-decoration:none;font-weight:700;">{label}</a>'
    ).format(url=rec_url, label=label)
    st.markdown(fallback, unsafe_allow_html=True)
    st.caption("You can keep chatting here or record your answer now.")


def render_chat_stage(
    *,
    client,
    db,
    highlight_words: Iterable[str],
    bubble_user: str,
    bubble_assistant: str,
    highlight_keywords: Callable[[str, Iterable[str]], str],
    generate_chat_pdf: Callable[[List[Dict[str, str]]], bytes],
    render_umlaut_pad: Callable[[str, str, bool], None],
) -> None:
    level = st.session_state.get("falowen_level")
    teil = st.session_state.get("falowen_teil")
    mode = st.session_state.get("falowen_mode")
    student_code = st.session_state.get("student_code", "demo")
    is_exam = mode == "Exams Mode"

    custom_chat.set_summary_client(client)

    key_fn = lambda base: widget_key(base, student_code=student_code)  # noqa: E731

    session = prepare_chat_session(
        db=db,
        student_code=student_code,
        mode=mode,
        level=level,
        teil=teil,
    )

    if session.fresh_chat:
        reset_falowen_chat_flow(clear_messages=False, clear_intro=False)

    if is_exam:
        topic = st.session_state.get("falowen_exam_topic")
        keyword = st.session_state.get("falowen_exam_keyword")
        prompts = exams_mode.build_exam_prompts(level, teil, topic, keyword, student_code)
        instruction = prompts.instruction or custom_chat.CUSTOM_CHAT_GREETING
        system_prompt = prompts.system_prompt
    else:
        instruction = custom_chat.CUSTOM_CHAT_GREETING
        system_prompt = custom_chat.build_custom_chat_prompt(level, student_code)

    seed_initial_instruction(
        instruction,
        student_code=student_code,
        conv_key=session.conv_key,
        db=db,
        doc_ref=session.doc_ref,
        doc_data=session.doc_data,
    )

    recorder_display = st.container()
    chat_display = st.container()
    status_display = st.container()
    status_placeholder = status_display.empty()

    def _render_chat_messages(container):
        with container:
            for msg in st.session_state.get("falowen_messages", []):
                if msg.get("role") == "assistant":
                    with st.chat_message("assistant", avatar="🧑‍🏫"):
                        st.markdown(
                            "<span style='color:#cddc39;font-weight:bold'>🧑‍🏫 Herr Felix:</span><br>"
                            f"<div style='{bubble_assistant}'>{highlight_keywords(msg.get('content', ''), highlight_words)}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    with st.chat_message("user"):
                        st.markdown(
                            "<div style='display:flex;justify-content:flex-end;'>"
                            f"<div style='{bubble_user}'>🗣️ {msg.get('content', '')}</div></div>",
                            unsafe_allow_html=True,
                        )

    with recorder_display:
        _render_recorder_button(key_fn, student_code)

    _render_chat_messages(chat_display)

    if is_exam:
        input_result = _render_exam_input_area(
            draft_key=session.draft_key,
            conv_key=session.conv_key,
            student_code=student_code,
            widget_key_fn=key_fn,
            render_umlaut_pad=render_umlaut_pad,
        )
        chat_locked = False
        use_chat_input = False
    else:
        custom_result = custom_chat.render_custom_chat_input(
            draft_key=session.draft_key,
            conv_key=session.conv_key,
            student_code=student_code,
            widget_key=key_fn,
            render_umlaut_pad=render_umlaut_pad,
        )
        input_result = ExamInputResult(
            user_input=custom_result.user_input,
            save_clicked=custom_result.save_clicked,
        )
        chat_locked = custom_result.chat_locked
        use_chat_input = custom_result.use_chat_input

    if input_result.save_clicked:
        save_now(session.draft_key, student_code)

    if input_result.user_input:
        st.session_state.setdefault("falowen_messages", []).append(
            {"role": "user", "content": input_result.user_input}
        )
        if not use_chat_input:
            st.session_state["falowen_clear_draft"] = True

        with status_placeholder:
            with st.spinner("🧑‍🏫 Herr Felix is typing…"):
                payload = [{"role": "system", "content": system_prompt}] + st.session_state["falowen_messages"]
                try:
                    resp = client.chat.completions.create(
                        model="gpt-4o",
                        messages=payload,
                        temperature=0.15,
                        max_tokens=600,
                    )
                    ai_reply = (resp.choices[0].message.content or "").strip()
                except Exception as exc:
                    ai_reply = f"Sorry, an error occurred: {exc}"

        status_placeholder.empty()

        st.session_state["falowen_messages"].append({"role": "assistant", "content": ai_reply})
        if not is_exam:
            custom_chat.increment_turn_count_and_maybe_close(False)
        else:
            st.session_state["falowen_chat_closed"] = False

        persist_messages(
            student_code,
            session.conv_key,
            st.session_state["falowen_messages"],
            db=db,
            doc_ref=session.doc_ref,
            doc_data=session.doc_data,
        )

        refreshed_chat_display = chat_display.empty()
        status_placeholder = status_display.empty()
        _render_chat_messages(refreshed_chat_display)

    teil_str = str(teil) if teil else "chat"
    pdf_bytes = generate_chat_pdf(st.session_state.get("falowen_messages", []))
    st.download_button(
        "⬇️ Download Chat as PDF",
        pdf_bytes,
        file_name=f"Falowen_Chat_{level}_{teil_str.replace(' ', '_')}.pdf",
        mime="application/pdf",
        key=key_fn("dl_chat_pdf"),
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🗑️ Delete All Chat History", key=key_fn("btn_delete_history")):
            if db is not None:
                try:
                    db.collection("falowen_chats").document(student_code).delete()
                except Exception as exc:
                    st.error(f"Could not delete chat history: {exc}")
                else:
                    for k in [
                        "falowen_stage",
                        "falowen_mode",
                        "falowen_level",
                        "falowen_teil",
                        "falowen_messages",
                        "custom_topic_intro_done",
                        "falowen_exam_topic",
                        "falowen_exam_keyword",
                        "_falowen_loaded",
                        "falowen_loaded_key",
                    ]:
                        st.session_state.pop(k, None)
                    st.session_state["falowen_stage"] = 1
                    rerun_without_toast()
    with col2:
        if st.button("🔁 Reset Chat", key=key_fn("reset_chat")):
            reset_falowen_chat_flow()
            rerun_without_toast()
    with col3:
        if st.button("⬅️ Back", key=key_fn("btn_back_stage4")):
            save_now(session.draft_key, student_code)
            back_step()

    st.divider()


__all__ = [
    "ChatSessionData",
    "ExamInputResult",
    "widget_key",
    "reset_falowen_chat_flow",
    "back_step",
    "prepare_chat_session",
    "persist_messages",
    "seed_initial_instruction",
    "render_chat_stage",
]
