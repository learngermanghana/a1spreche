from unittest.mock import MagicMock
import types
import time

from src import draft_management as dm


def test_on_cb_subtab_change_save_error(monkeypatch):
    mock_st = types.SimpleNamespace(
        session_state={
            "__cb_subtab_prev": "🧑‍🏫 Classroom",
            "coursebook_subtab": "Other",
            "student_code": "code",
            "classroom_reply_draft_1": "hi",
        }
    )
    monkeypatch.setattr(dm, "st", mock_st)
    monkeypatch.setattr(dm, "save_draft_to_db", MagicMock(side_effect=Exception("boom")))
    toast_mock = MagicMock()
    monkeypatch.setattr(dm, "toast_err", toast_mock)
    dm.on_cb_subtab_change()
    toast_mock.assert_called_once_with("Draft save failed")


def test_autosave_learning_note_requires_student_code(monkeypatch):
    errors = []
    mock_st = types.SimpleNamespace(session_state={}, error=lambda msg: errors.append(msg))
    monkeypatch.setattr(dm, "st", mock_st)
    save_mock = MagicMock()
    monkeypatch.setattr(dm, "save_notes_to_db", save_mock)
    dm.autosave_learning_note("", "notes_key")
    assert errors
    save_mock.assert_not_called()


def test_autosave_maybe_handles_none_state(monkeypatch):
    draft_key = "lesson_field"
    last_val_key, last_ts_key, saved_flag_key, saved_at_key = dm._draft_state_keys(draft_key)
    session_state = {
        last_val_key: None,
        last_ts_key: 0.0,
        "falowen_chat_draft_key": "other",
    }
    mock_st = types.SimpleNamespace(session_state=session_state)
    monkeypatch.setattr(dm, "st", mock_st)

    save_mock = MagicMock()
    monkeypatch.setattr(dm, "save_draft_to_db", save_mock)
    monkeypatch.setattr(dm, "save_chat_draft_to_db", MagicMock())

    dm.autosave_maybe("code", draft_key, None, min_secs=0)
    dm.autosave_maybe("code", draft_key, "New text", min_secs=0)

    save_mock.assert_called_once_with("code", draft_key, "New text")
    assert session_state[last_val_key] == "New text"
    assert session_state[last_ts_key] >= 0.0
    assert session_state[saved_flag_key] is True
    assert saved_at_key in session_state


def test_save_before_download_persists_and_skips(monkeypatch):
    draft_key = "draft_A1_day1_ch1"
    session_state = {draft_key: "Hello"}
    mock_st = types.SimpleNamespace(session_state=session_state)
    monkeypatch.setattr(dm, "st", mock_st)

    save_calls = []
    monkeypatch.setattr(dm, "save_draft_to_db", lambda code, key, text: save_calls.append((code, key, text)))
    chat_mock = MagicMock()
    monkeypatch.setattr(dm, "save_chat_draft_to_db", chat_mock)

    dm.save_before_download(draft_key, "STUDENT42")

    assert save_calls == [("STUDENT42", draft_key, "Hello")]
    chat_mock.assert_not_called()

    last_val_key, last_ts_key, saved_flag_key, saved_at_key = dm._draft_state_keys(draft_key)
    assert session_state[last_val_key] == "Hello"
    assert session_state[last_ts_key] <= time.time()
    assert session_state[saved_flag_key] is True
    assert saved_at_key in session_state

    # skip counter should cover the next two saves
    assert dm._consume_skip_counter(draft_key) is True
    assert dm._consume_skip_counter(draft_key) is True
    assert dm._consume_skip_counter(draft_key) is False

    # existing skip counters are preserved when saving again
    dm.skip_next_save(draft_key, count=1)
    session_state[draft_key] = "Updated"
    dm.save_before_download(draft_key, "STUDENT42", skip_count=1)
    assert save_calls[-1] == ("STUDENT42", draft_key, "Updated")

    assert dm._consume_skip_counter(draft_key) is True
    assert dm._consume_skip_counter(draft_key) is True
    assert dm._consume_skip_counter(draft_key) is False
