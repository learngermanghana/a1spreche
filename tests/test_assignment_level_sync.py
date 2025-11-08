"""Tests for synchronising Assignment Helper level state."""

from src.level_sync import sync_assignment_level_state


LEVEL_OPTIONS = ["A1", "A2", "B1", "B2", "C1"]
ASSIGN_KEY = "assign_level"


def test_sync_assignment_level_sets_detected_level_for_new_student():
    session = {}

    result = sync_assignment_level_state(
        session,
        student_code="abc123",
        detected_level="B1",
        level_options=LEVEL_OPTIONS,
        assign_key=ASSIGN_KEY,
    )

    assert result == "B1"
    assert session[ASSIGN_KEY] == "B1"
    assert session["_assign_last_student_code"] == "abc123"
    assert session["_assign_last_detected_level"] == "B1"


def test_sync_assignment_level_retains_manual_selection_when_roster_unchanged():
    session = {}
    sync_assignment_level_state(
        session,
        student_code="abc123",
        detected_level="B2",
        level_options=LEVEL_OPTIONS,
        assign_key=ASSIGN_KEY,
    )
    session[ASSIGN_KEY] = "C1"

    result = sync_assignment_level_state(
        session,
        student_code="abc123",
        detected_level="B2",
        level_options=LEVEL_OPTIONS,
        assign_key=ASSIGN_KEY,
    )

    assert result == "C1"
    assert session[ASSIGN_KEY] == "C1"


def test_sync_assignment_level_updates_when_detected_level_changes():
    session = {}
    sync_assignment_level_state(
        session,
        student_code="abc123",
        detected_level="B2",
        level_options=LEVEL_OPTIONS,
        assign_key=ASSIGN_KEY,
    )
    session[ASSIGN_KEY] = "C1"

    result = sync_assignment_level_state(
        session,
        student_code="abc123",
        detected_level="A2",
        level_options=LEVEL_OPTIONS,
        assign_key=ASSIGN_KEY,
    )

    assert result == "A2"
    assert session[ASSIGN_KEY] == "A2"


def test_sync_assignment_level_invalid_detected_level_falls_back_to_first_option():
    session = {}

    result = sync_assignment_level_state(
        session,
        student_code="xyz",
        detected_level="Z9",
        level_options=LEVEL_OPTIONS,
        assign_key=ASSIGN_KEY,
    )

    assert result == LEVEL_OPTIONS[0]
    assert session[ASSIGN_KEY] == LEVEL_OPTIONS[0]
