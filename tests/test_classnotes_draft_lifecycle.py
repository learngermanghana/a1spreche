import types  # required for types.SimpleNamespace
from datetime import datetime
from unittest.mock import MagicMock

from src import draft_management as dm


def test_autosave_wrapper_invokes_autosave(monkeypatch):
    session_state = {}
    monkeypatch.setattr(dm, "st", types.SimpleNamespace(session_state=session_state))
    monkeypatch.setattr(
        dm,
        "load_draft_meta_from_db",
        MagicMock(return_value=("existing draft", None)),
    )

    dm.initialize_draft_state("code", "q_text")

    autosave_mock = MagicMock()
    monkeypatch.setattr(dm, "autosave_maybe", autosave_mock)

    dm.autosave_draft_for_text(
        "code",
        "q_text",
        "updated",
        min_secs=0.0,
        min_delta=0,
    )

    autosave_mock.assert_called_once_with(
        "code",
        "q_text",
        "updated",
        min_secs=0.0,
        min_delta=0,
        locked=False,
    )


def test_clear_draft_after_post_resets_local_state(monkeypatch):
    session_state = {}
    monkeypatch.setattr(dm, "st", types.SimpleNamespace(session_state=session_state))

    dm.reset_local_draft_state(
        "q_text",
        text="to publish",
        saved=True,
        saved_at=datetime.now(),
    )

    save_mock = MagicMock()
    monkeypatch.setattr(dm, "save_draft_to_db", save_mock)

    dm.clear_draft_after_post("code", "q_text")

    last_val_key, last_ts_key, saved_flag_key, saved_at_key = dm._draft_state_keys(
        "q_text"
    )

    assert "q_text" not in session_state
    assert session_state[last_val_key] == ""
    assert session_state[saved_flag_key] is False
    assert session_state[saved_at_key] is None
    assert last_ts_key in session_state

    save_mock.assert_called_once_with("code", "q_text", "")
