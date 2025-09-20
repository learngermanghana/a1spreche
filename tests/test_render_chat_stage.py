import pytest

from src.falowen import chat_core


class _FakeStreamlit:
    def __init__(self, *, session_state, selected_key):
        self.session_state = session_state
        self._selected_key = selected_key
        self.selectbox_calls = []

    def selectbox(self, *args, **kwargs):
        self.selectbox_calls.append((args, kwargs))
        return self._selected_key


def test_render_chat_stage_switch_does_not_persist_previous_chat(monkeypatch):
    current_key = "Chat Mode_A1_custom_oldconv"
    next_key = "Chat Mode_A1_custom_newconv"
    session_state = {
        "falowen_level": "A1",
        "falowen_teil": None,
        "falowen_mode": "Chat Mode",
        "student_code": "stu1",
        "falowen_conv_key": current_key,
        "falowen_messages": [{"role": "assistant", "content": "Hallo"}],
    }
    fake_st = _FakeStreamlit(session_state=session_state, selected_key=next_key)
    monkeypatch.setattr(chat_core, "st", fake_st)

    session = chat_core.ChatSessionData(
        conv_key=current_key,
        draft_key="draft",
        doc_ref=None,
        doc_data={
            "chats": {
                current_key: [{"role": "assistant", "content": "Hallo"}],
                next_key: [{"role": "assistant", "content": "Servus"}],
            }
        },
        fresh_chat=False,
    )
    monkeypatch.setattr(chat_core, "prepare_chat_session", lambda **_: session)

    rerun_called = False

    def fake_rerun():
        nonlocal rerun_called
        rerun_called = True

    monkeypatch.setattr(chat_core, "rerun_without_toast", fake_rerun)

    persist_calls = []
    monkeypatch.setattr(chat_core, "persist_messages", lambda *args, **kwargs: persist_calls.append((args, kwargs)))
    monkeypatch.setattr(
        chat_core,
        "seed_initial_instruction",
        lambda *args, **kwargs: pytest.fail("seed_initial_instruction should not run"),
    )

    chat_core.render_chat_stage(
        client=None,
        db=None,
        highlight_words=(),
        bubble_user="",
        bubble_assistant="",
        highlight_keywords=lambda value, _: value,
        generate_chat_pdf=lambda _: b"",
        render_umlaut_pad=lambda *args, **kwargs: None,
    )

    assert rerun_called is True
    assert persist_calls == []
    assert session_state["falowen_conv_key"] == next_key
    assert "falowen_messages" not in session_state
    assert session_state["falowen_clear_draft"] is True


def test_combine_history_for_display_includes_all_threads():
    threads = [
        (
            "Chat Mode_A1_custom_old",
            [
                {"role": "assistant", "content": "old-1"},
                {"role": "user", "content": "old-2"},
            ],
        ),
        (
            "Chat Mode_A1_custom_archived",
            [
                {"role": "assistant", "content": "archived-1"},
            ],
        ),
    ]
    current_messages = [
        {"role": "assistant", "content": "current-1"},
        {"role": "user", "content": "current-2"},
    ]

    combined = chat_core.combine_history_for_display(
        threads,
        current_conv_key="Chat Mode_A1_custom_active",
        current_messages=current_messages,
    )

    divider_labels = [msg["content"] for msg in combined if msg.get("_divider")]
    assert len(divider_labels) == 3

    rendered_messages = [msg["content"] for msg in combined if not msg.get("_divider")]
    assert rendered_messages == [
        "old-1",
        "old-2",
        "archived-1",
        "current-1",
        "current-2",
    ]
