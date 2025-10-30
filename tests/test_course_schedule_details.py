from datetime import date

from src.course_schedule import next_session_details


def test_next_session_details_returns_first_future_day():
    details = next_session_details("A1 Munich Klasse", from_date=date(2025, 9, 16))

    assert details is not None
    assert details["date"] == date(2025, 9, 17)
    assert details["day_number"] == 1
    assert details["summary"]
    assert details["summary"].startswith("Day 1 — ")
    assert any("Chapter 0.1" in label for label in details["sessions"])


def test_next_session_details_skips_to_second_day_when_first_passed():
    details = next_session_details("A1 Munich Klasse", from_date=date(2025, 9, 18))

    assert details is not None
    assert details["date"] == date(2025, 9, 22)
    assert details["day_number"] == 2
    assert details["summary"] and details["summary"].startswith("Day 2 — ")
    assert any("Chapter 0.2" in label for label in details["sessions"])
