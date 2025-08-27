from src.schedule import load_level_schedules, get_level_schedules


def test_load_level_schedules_has_levels():
    schedules = load_level_schedules()
    assert set(schedules.keys()) >= {"A1", "A2", "B1", "B2", "C1"}


def test_get_level_schedules_matches_load():
    assert get_level_schedules() == load_level_schedules()
