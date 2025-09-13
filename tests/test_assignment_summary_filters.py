import pandas as pd

from src import assignment_ui


def test_next_assignment_skips_goethe_and_final_cap(monkeypatch):
    schedule = [
        {"day": 1, "chapter": "1.0", "assignment": True, "topic": "Ch1"},
        {"day": 2, "chapter": "1.5", "assignment": True, "topic": "Goethe practice"},
        {"day": 3, "chapter": "14.2", "assignment": True, "topic": "Beyond"},
        {"day": 4, "chapter": "2.0", "assignment": True, "topic": "Ch2"},
    ]
    df = pd.DataFrame(
        {
            "studentcode": ["s1"],
            "assignment": ["1.0"],
            "level": ["A1"],
            "score": ["90"],
            "date": ["2024-01-01"],
        }
    )
    monkeypatch.setattr(assignment_ui, "_get_level_schedules", lambda: {"A1": schedule})

    summary = assignment_ui.get_assignment_summary("s1", "A1", df)
    assert summary["missed"] == []
    assert summary["next"]["day"] == 4


def test_missed_assignments_skip_goethe(monkeypatch):
    schedule = [
        {"day": 1, "chapter": "1.0", "assignment": True, "topic": "Goethe intro"},
        {"day": 2, "chapter": "2.0", "assignment": True, "topic": "Ch2"},
        {"day": 3, "chapter": "3.0", "assignment": True, "topic": "Ch3"},
    ]
    df = pd.DataFrame(
        {
            "studentcode": ["s1"],
            "assignment": ["2.0"],
            "level": ["A1"],
            "score": ["90"],
            "date": ["2024-01-01"],
        }
    )
    monkeypatch.setattr(assignment_ui, "_get_level_schedules", lambda: {"A1": schedule})

    summary = assignment_ui.get_assignment_summary("s1", "A1", df)
    assert summary["missed"] == []
    assert summary["next"]["day"] == 3


def test_skipped_detection_includes_nested_assignments(monkeypatch):
    schedule = [
        {"day": 1, "chapter": "1.0", "assignment": True, "topic": "Ch1"},
        {
            "day": 2,
            "chapter": "1.5",
            "topic": "Ch1.5",
            "lesen_hören": [{"chapter": "1.5", "assignment": True}],
        },
        {"day": 3, "chapter": "2.0", "assignment": True, "topic": "Ch2"},
    ]
    df = pd.DataFrame(
        {
            "studentcode": ["s1", "s1"],
            "assignment": ["1.0", "2.0"],
            "level": ["A1", "A1"],
            "score": ["90", "95"],
            "date": ["2024-01-01", "2024-01-02"],
        }
    )
    monkeypatch.setattr(assignment_ui, "_get_level_schedules", lambda: {"A1": schedule})

    summary = assignment_ui.get_assignment_summary("s1", "A1", df)
    assert summary["missed"] == ["Day 2: Chapter 1.5 – Ch1.5"]
