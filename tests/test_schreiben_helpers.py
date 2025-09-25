"""Tests for schreiben helper functions with empty student code."""

import importlib
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def helpers(monkeypatch):
    import src.schreiben as schreiben
    mod = importlib.reload(schreiben)
    monkeypatch.setattr(mod, "st", MagicMock())
    monkeypatch.setattr(mod, "db", MagicMock())
    monkeypatch.setattr(mod, "FieldFilter", MagicMock())
    monkeypatch.setattr(mod, "firestore", MagicMock())
    return mod


def test_update_schreiben_stats_empty(helpers):
    helpers.update_schreiben_stats("")
    helpers.db.collection.assert_not_called()
    helpers.st.warning.assert_called_once()


def test_get_schreiben_stats_empty(helpers):
    stats = helpers.get_schreiben_stats("")
    helpers.db.collection.assert_not_called()
    helpers.st.warning.assert_called_once()
    assert stats == {
        "total": 0,
        "passed": 0,
        "average_score": 0,
        "best_score": 0,
        "pass_rate": 0,
        "last_attempt": None,
        "attempts": [],
        "last_letter": "",
    }


def test_save_schreiben_feedback_empty(helpers):
    helpers.save_schreiben_feedback("", "fb", "letter")
    helpers.db.collection.assert_not_called()
    helpers.st.warning.assert_called_once()


def test_load_schreiben_feedback_empty(helpers):
    result = helpers.load_schreiben_feedback("")
    helpers.db.collection.assert_not_called()
    helpers.st.warning.assert_called_once()
    assert result == ("", "")


def test_delete_schreiben_feedback_empty(helpers):
    helpers.delete_schreiben_feedback("")
    helpers.db.collection.assert_not_called()
    helpers.st.warning.assert_called_once()


def test_delete_schreiben_feedback_clears_record(helpers):
    doc = helpers.db.collection.return_value.document.return_value
    doc.get.return_value.exists = False
    helpers.delete_schreiben_feedback("abc")
    result = helpers.load_schreiben_feedback("abc")
    doc.delete.assert_called_once_with()
    helpers.st.warning.assert_not_called()
    assert result == ("", "")


def test_save_submission_empty(helpers):
    helpers.save_submission("", 50, True, None, "A1", "L")
    helpers.db.collection.assert_not_called()
    helpers.st.warning.assert_called_once()


def test_save_submission_valid(helpers):
    helpers.save_submission("abc", 75, False, None, "A1", "text")
    helpers.db.collection.assert_called_once_with("schreiben_submissions")
    helpers.db.collection.return_value.add.assert_called_once()
    data = helpers.db.collection.return_value.add.call_args[0][0]
    assert data["student_code"] == "abc"
    assert data["score"] == 75
    assert data["passed"] is False
    assert data["level"] == "A1"
    assert data["letter"] == "text"


def test_get_schreiben_usage(helpers):
    doc = helpers.db.collection.return_value.document.return_value.get.return_value
    doc.exists = True
    doc.to_dict.return_value = {"count": 3}
    assert helpers.get_schreiben_usage("abc") == 3
    helpers.db.collection.assert_called_with("schreiben_usage")


def test_inc_schreiben_usage_updates_or_creates(helpers):
    doc = helpers.db.collection.return_value.document.return_value.get.return_value
    doc.exists = False
    helpers.inc_schreiben_usage("abc")
    helpers.db.collection.return_value.document.return_value.get.assert_called_once()
    helpers.db.collection.return_value.document.return_value.set.assert_called_once()
