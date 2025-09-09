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
    toast_mock.assert_called_once_with("Draft save failed")
