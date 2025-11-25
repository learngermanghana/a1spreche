from datetime import date

from src.course_schedule import next_session_details


def test_next_session_details_returns_first_future_day():
    details = next_session_details("A1 Frankfurt Klasse", from_date=date(2025, 10, 22))

    assert details is not None
    assert details["date"] == date(2025, 10, 23)
    assert details["day_number"] == 1
    assert details["summary"]
    assert details["summary"].startswith("Day 1 — ")
    assert any("Chapter 0.1" in label for label in details["sessions"])


def test_next_session_details_skips_to_second_day_when_first_passed():
    details = next_session_details("A1 Frankfurt Klasse", from_date=date(2025, 10, 24))

    assert details is not None
    assert details["date"] == date(2025, 10, 24)
    assert details["day_number"] == 2
    assert details["summary"] and details["summary"].startswith("Day 2 — ")
    assert any("Chapter 0.2" in label for label in details["sessions"])
