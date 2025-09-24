from unittest.mock import MagicMock
import types

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
    toast_mock.assert_called_once_with(dm.DRAFT_SAVE_FAILED_MSG)


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


def test_save_now_surfaces_failure(monkeypatch):
    draft_key = "lesson_field"
    last_val_key, last_ts_key, saved_flag_key, saved_at_key = dm._draft_state_keys(
        draft_key
    )
    session_state = {draft_key: "New text", "falowen_chat_draft_key": "other"}
    mock_st = types.SimpleNamespace(session_state=session_state)
    monkeypatch.setattr(dm, "st", mock_st)

    monkeypatch.setattr(dm, "save_draft_to_db", MagicMock(return_value=False))
    monkeypatch.setattr(dm, "save_chat_draft_to_db", MagicMock(return_value=False))
    toast_mock = MagicMock()
    monkeypatch.setattr(dm, "toast_err", toast_mock)

    dm.save_now(draft_key, "code")

    toast_mock.assert_called_once_with(dm.DRAFT_SAVE_FAILED_MSG)
    assert session_state.get(saved_flag_key) is False
    assert last_val_key not in session_state
    assert last_ts_key not in session_state
    assert saved_at_key not in session_state


def test_autosave_maybe_surfaces_failure(monkeypatch):
    draft_key = "lesson_field"
    last_val_key, last_ts_key, saved_flag_key, saved_at_key = dm._draft_state_keys(
        draft_key
    )
    session_state = {
        last_val_key: "old",
        last_ts_key: 0.0,
        saved_flag_key: True,
        "falowen_chat_draft_key": "other",
    }
    mock_st = types.SimpleNamespace(session_state=session_state)
    monkeypatch.setattr(dm, "st", mock_st)

    monkeypatch.setattr(dm, "save_draft_to_db", MagicMock(return_value=False))
    monkeypatch.setattr(dm, "save_chat_draft_to_db", MagicMock(return_value=False))
    toast_once_mock = MagicMock()
    monkeypatch.setattr(dm, "toast_once", toast_once_mock)

    dm.autosave_maybe("code", draft_key, "New text", min_secs=0)

    toast_once_mock.assert_called_once_with(dm.DRAFT_SAVE_FAILED_MSG, "❌")
    assert session_state[last_val_key] == "old"
    assert session_state[last_ts_key] >= 0.0
    assert session_state[saved_flag_key] is False
    assert saved_at_key not in session_state
