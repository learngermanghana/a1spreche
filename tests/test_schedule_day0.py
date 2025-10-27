"""Tests covering the shared Day 0 tutorial schedule entry."""

from src.schedule import (
    DAY0_TUTORIAL_VIDEO_URL_ADVANCED,
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


def test_day0_orientation_uses_advanced_video_url():
    """The shared Day 0 entry should point to the advanced tutorial video."""

    orientation_entry = make_day0_tutorial_entry()

    assert orientation_entry["tutorial_video_url"] == DAY0_TUTORIAL_VIDEO_URL_ADVANCED
    assert orientation_entry["lesen_hören"]["video"] == DAY0_TUTORIAL_VIDEO_URL_ADVANCED
    assert orientation_entry["lesen_hören"]["youtube_link"] == DAY0_TUTORIAL_VIDEO_URL_ADVANCED


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
