"""Tests covering the shared Day 0 tutorial schedule entry."""

from src.schedule import (
    _strip_topic_chapter,
    get_b2_schedule,
    make_day0_tutorial_entry,
)


def test_b2_schedule_starts_with_full_day0_orientation():
    """The B2 plan should begin with the full Day 0 tutorial entry only once."""

    schedule = get_b2_schedule()
    orientation_entry = make_day0_tutorial_entry()

    assert schedule[0] == orientation_entry
    assert sum(1 for item in schedule if item.get("day") == 0) == 1


def test_strip_topic_chapter_trims_trailing_chapter_numbers():
    """``_strip_topic_chapter`` should remove duplicated chapter numbers only when trailing."""

    data = [
        {"day": 1, "topic": "Mein Lieblingssport 6.15", "chapter": "6.15"},
        {"day": 2, "topic": "Tutorial – Course Overview", "chapter": "Tutorial"},
        {"day": 3, "topic": "Extra whitespace   4.4", "chapter": "4.4"},
        {"day": 4, "topic": "Already clean", "chapter": "1.1"},
    ]

    cleaned = _strip_topic_chapter(data)

    assert cleaned[0]["topic"] == "Mein Lieblingssport"
    assert cleaned[1]["topic"] == "Tutorial – Course Overview"
    assert cleaned[2]["topic"] == "Extra whitespace"
    assert cleaned[3]["topic"] == "Already clean"
