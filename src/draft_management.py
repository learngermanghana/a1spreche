"""Draft management helpers.

Functions for saving and restoring text drafts and learning notes. These were
previously defined inline in ``a1sprechen.py`` but have been extracted into a
module so they can be reused and tested independently.
"""

from datetime import datetime, timezone as _timezone
import time
from typing import Tuple

import streamlit as st

from falowen.sessions import db
from src.firestore_utils import save_chat_draft_to_db, save_draft_to_db
from src.utils.toasts import toast_ok


def _draft_state_keys(draft_key: str) -> Tuple[str, str, str, str]:
    """Return the session-state keys used to track last save info for a draft."""
    return (
        f"{draft_key}__last_val",
        f"{draft_key}__last_ts",
        f"{draft_key}_saved",
        f"{draft_key}_saved_at",
    )


def save_now(draft_key: str, code: str) -> None:
    """Immediately persist the draft associated with ``draft_key``."""
    text = st.session_state.get(draft_key, "") or ""
    if st.session_state.get("falowen_chat_draft_key") == draft_key:
        conv = st.session_state.get("falowen_conv_key", "")
        save_chat_draft_to_db(code, conv, text)
    else:
        save_draft_to_db(code, draft_key, text)

    last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(
        draft_key
    )
    st.session_state[last_val_key] = text
    st.session_state[last_ts_key] = time.time()
    st.session_state[saved_flag_key] = True
    st.session_state[saved_at_key] = datetime.now(_timezone.utc)
    toast_ok("Saved!")


def autosave_maybe(
    code: str,
    lesson_field_key: str,
    text: str,
    *,
    min_secs: float = 5.0,
    min_delta: int = 30,
    locked: bool = False,
) -> None:
    """Debounced background autosave for lesson drafts."""
    if locked:
        return

    last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(
        lesson_field_key
    )
    last_val = st.session_state.get(last_val_key, "")
    last_ts = float(st.session_state.get(last_ts_key, 0.0))
    now = time.time()

    changed = text != last_val
    big_change = abs(len(text) - len(last_val)) >= min_delta
    time_ok = (now - last_ts) >= min_secs

    if changed and (time_ok or big_change):
        if st.session_state.get("falowen_chat_draft_key") == lesson_field_key:
            conv = st.session_state.get("falowen_conv_key", "")
            save_chat_draft_to_db(code, conv, text)
        else:
            save_draft_to_db(code, lesson_field_key, text)
        st.session_state[last_val_key] = text
        st.session_state[last_ts_key] = now
        st.session_state[saved_flag_key] = True
        st.session_state[saved_at_key] = datetime.now(_timezone.utc)


def load_notes_from_db(student_code):
    ref = db.collection("learning_notes").document(student_code)
    doc = ref.get()
    return doc.to_dict().get("notes", []) if doc.exists else []


def save_notes_to_db(student_code, notes):
    ref = db.collection("learning_notes").document(student_code)
    ref.set({"notes": notes}, merge=True)


def autosave_learning_note(student_code: str, key_notes: str) -> None:
    """Autosave the current learning note draft to Firestore."""
    notes = st.session_state.get(key_notes, [])
    idx = st.session_state.get("edit_note_idx")
    draft = st.session_state.get("learning_note_draft", "")
    title = st.session_state.get("learning_note_title", "")
    tag = st.session_state.get("learning_note_tag", "")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    note = {
        "title": title.strip().title(),
        "tag": tag.strip().title(),
        "text": draft.strip(),
        "pinned": False,
        "created": ts,
        "updated": ts,
    }

    if idx is not None and idx < len(notes):
        existing = notes[idx]
        note["pinned"] = existing.get("pinned", False)
        note["created"] = existing.get("created", ts)
        notes[idx] = note
    else:
        notes.insert(0, note)
        st.session_state["edit_note_idx"] = 0

    st.session_state[key_notes] = notes
    save_notes_to_db(student_code, notes)
    st.session_state["learning_note_last_saved"] = ts


def on_cb_subtab_change() -> None:
    """Save or restore classroom reply drafts when switching subtabs."""
    prev = st.session_state.get("__cb_subtab_prev")
    curr = st.session_state.get("coursebook_subtab")
    code = st.session_state.get("student_code", "")

    if prev == "🧑‍🏫 Classroom" and curr != "🧑‍🏫 Classroom":
        for key in [k for k in st.session_state.keys() if k.startswith("classroom_reply_draft_")]:
            try:
                save_draft_to_db(code, key, st.session_state.get(key, ""))
            except Exception:
                pass
            last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(
                key
            )
            for k in (key, last_val_key, last_ts_key, saved_flag_key, saved_at_key):
                st.session_state.pop(k, None)

    elif curr == "🧑‍🏫 Classroom" and prev != "🧑‍🏫 Classroom":
        try:
            lessons = db.collection("drafts_v2").document(code).collection("lessons")
            for doc in lessons.stream():
                if doc.id.startswith("classroom_reply_draft_"):
                    data = doc.to_dict() or {}
                    text = data.get("text", "")
                    ts = data.get("updated_at")
                    st.session_state[doc.id] = text
                    last_val_key, last_ts_key, saved_flag_key, saved_at_key = _draft_state_keys(
                        doc.id
                    )
                    st.session_state[last_val_key] = text
                    st.session_state[last_ts_key] = time.time()
                    st.session_state[saved_flag_key] = bool(text)
                    st.session_state[saved_at_key] = ts
        except Exception:
            pass

    st.session_state["__cb_subtab_prev"] = curr


__all__ = [
    "_draft_state_keys",
    "save_now",
    "autosave_maybe",
    "load_notes_from_db",
    "save_notes_to_db",
    "autosave_learning_note",
    "on_cb_subtab_change",
]
