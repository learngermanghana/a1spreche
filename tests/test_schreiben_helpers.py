"""Tests for schreiben helper functions with empty student code."""

import importlib
from unittest.mock import MagicMock

import pytest

import src.schreiben as schreiben

@pytest.fixture
def helpers(monkeypatch):
    mod = importlib.reload(schreiben)
    monkeypatch.setattr(mod, "st", MagicMock())
    monkeypatch.setattr(mod, "db", MagicMock())
    monkeypatch.setattr(mod, "FieldFilter", MagicMock())
    monkeypatch.setattr(mod, "firestore", MagicMock())
    monkeypatch.setattr(mod, "date", MagicMock())

    mod.date.today = MagicMock()
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
    helpers.db.collection.return_value.add.assert_called_once_with(
        {
            "student_code": "abc",
            "score": 75,
            "passed": False,
            "date": helpers.firestore.SERVER_TIMESTAMP,
            "level": "A1",
            "letter": "text",
        }
    )
    helpers.st.warning.assert_not_called()

def test_get_letter_coach_usage_empty(helpers):
    count = helpers.get_letter_coach_usage("")
    helpers.db.collection.assert_not_called()
    helpers.date.today.assert_not_called()
    helpers.st.warning.assert_called_once()
    assert count == 0
