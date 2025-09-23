from unittest.mock import MagicMock
import types

from src.logout import do_logout


def test_logout_clears_all_draft_state():
    session_state = {
        "draft_sample": "draft",
        "draft_sample__last_val": "draft",
        "draft_sample__pending_reload": True,
        "coursebook_draft_key": "draft_sample",
        "coursebook_draft_key__hydrated_v2": True,
        "coursebook_draft_key_saved": True,
        "__active_draft_key": "draft_sample",
        "__active_draft_key__last_ts": 123,
        "falowen_chat_draft_key": "falowen_chat_draft_1",
        "falowen_chat_draft_key__reload_text": "hello",
        "falowen_chat_draft_key__pending_reload": True,
        "falowen_chat_draft_topic": "Hi",
        "falowen_chat_draft_topic__last_val": "Hi",
        "unrelated": "keep",
        "another_key_saved": True,
    }

    success_calls = {}

    def success(message: str) -> None:
        success_calls["message"] = message
        assert all(not k.startswith("draft_") for k in session_state)
        assert "coursebook_draft_key" not in session_state
        assert "__active_draft_key" not in session_state
        assert "falowen_chat_draft_key" not in session_state
        assert all(
            not k.startswith("falowen_chat_draft_") for k in session_state
        )

    mock_st = types.SimpleNamespace(
        session_state=session_state,
        query_params={},
        success=success,
    )

    do_logout(
        st_module=mock_st,
        destroy_token=MagicMock(),
        logger=types.SimpleNamespace(exception=MagicMock()),
    )

    assert success_calls["message"] == "You’ve been logged out."
    assert "draft_sample" not in session_state
    assert "draft_sample__last_val" not in session_state
    assert "draft_sample__pending_reload" not in session_state
    assert "coursebook_draft_key" not in session_state
    assert "coursebook_draft_key__hydrated_v2" not in session_state
    assert "coursebook_draft_key_saved" not in session_state
    assert "__active_draft_key" not in session_state
    assert "__active_draft_key__last_ts" not in session_state
    assert "falowen_chat_draft_key" not in session_state
    assert "falowen_chat_draft_key__reload_text" not in session_state
    assert "falowen_chat_draft_key__pending_reload" not in session_state
    assert "falowen_chat_draft_topic" not in session_state
    assert "falowen_chat_draft_topic__last_val" not in session_state

    assert session_state["unrelated"] == "keep"
    assert session_state["another_key_saved"] is True
    assert session_state["logged_in"] is False
    assert session_state["student_row"] == {}
    assert session_state["student_code"] == ""
    assert session_state["student_name"] == ""
    assert session_state["session_token"] == ""
    assert session_state["student_level"] == ""
    assert session_state["need_rerun"] is True
