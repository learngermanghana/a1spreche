from src.schedule import (
    load_level_schedules,
    get_level_schedules,
    get_a1_schedule,
    get_a2_schedule,
    get_b1_schedule,
    get_b2_schedule,
    full_lesson_title,
)


def test_load_level_schedules_has_levels():
    schedules = load_level_schedules()
    assert set(schedules.keys()) >= {"A1", "A2", "B1", "B2", "C1"}


def test_get_level_schedules_matches_load():
    assert get_level_schedules() == load_level_schedules()


def test_get_a1_schedule_is_list():
    assert isinstance(get_a1_schedule(), list)


def test_get_a2_schedule_has_day0():
    schedule = get_a2_schedule()
    assert schedule[0]["day"] == 0
    assert schedule[0]["topic"] == "Tutorial – Course Overview"


def test_get_b1_schedule_has_day0():
    schedule = get_b1_schedule()
    assert schedule[0]["day"] == 0
    assert schedule[0]["topic"] == "Tutorial – Course Overview"


def test_get_b2_schedule_has_day0():
    schedule = get_b2_schedule()
    assert schedule[0]["day"] == 0
    assert schedule[0]["topic"] == "Tutorial – Course Overview"


def test_day15_title_normalized():
    schedules = load_level_schedules()
    day15 = next(d for d in schedules["A2"] if d["day"] == 15)
    assert (
        full_lesson_title(day15)
        == "Day 15: Mein Lieblingssport (Chapter 6.15)"
    )


def test_day6_coursebook_entry():
    schedule = get_a1_schedule()
    day6 = next(d for d in schedule if d["day"] == 6)
    label = f"Day {day6['day']} - {day6['topic']} {day6['chapter']}".strip()
    assert label == "Day 6 - Schreiben & Sprechen 2.3"
