"""Tests for schreiben helper functions with empty student code."""

import ast
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


TARGETS = {
    "update_schreiben_stats",
    "get_schreiben_stats",
    "save_schreiben_feedback",
    "load_schreiben_feedback",
    "get_letter_coach_usage",
}


def _load_helpers():
    source = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    tree = ast.parse(source.read_text(), filename=str(source))
    mod = types.ModuleType("helpers")
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in TARGETS:
            func_mod = ast.Module(body=[node], type_ignores=[])
            code = compile(func_mod, filename=str(source), mode="exec")
            exec(code, mod.__dict__)
    return mod


@pytest.fixture
def helpers():
    mod = _load_helpers()
    mod.st = MagicMock()
    mod.db = MagicMock()
    mod.FieldFilter = MagicMock()
    mod.firestore = MagicMock()
    mod.date = MagicMock()
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

def test_get_letter_coach_usage_empty(helpers):
    count = helpers.get_letter_coach_usage("")
    helpers.db.collection.assert_not_called()
    helpers.date.today.assert_not_called()
    helpers.st.warning.assert_called_once()
    assert count == 0
