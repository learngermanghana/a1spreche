import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.schedule import (
    load_level_schedules,
    get_level_schedules,
    get_a1_schedule,
    get_a2_schedule,
    get_b1_schedule,
    get_b2_schedule,
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
