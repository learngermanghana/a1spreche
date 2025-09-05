from src.schedule import (
    load_level_schedules,
    get_level_schedules,
    get_a1_schedule,
)


def test_load_level_schedules_has_levels():
    schedules = load_level_schedules()
    assert set(schedules.keys()) >= {"A1", "A2", "B1", "B2", "C1"}


def test_get_level_schedules_matches_load():
    assert get_level_schedules() == load_level_schedules()


def test_get_a1_schedule_is_list():
    assert isinstance(get_a1_schedule(), list)
