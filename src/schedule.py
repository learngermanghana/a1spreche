"""Simplified course schedule utilities for tests."""
from __future__ import annotations

from typing import Dict, List

ScheduleEntry = dict

def _tutorial_entry() -> ScheduleEntry:
    return {"day": 0, "topic": "Tutorial – Course Overview"}

def get_a1_schedule() -> List[ScheduleEntry]:
    return [_tutorial_entry()]

def get_a2_schedule() -> List[ScheduleEntry]:
    return [_tutorial_entry()]

def get_b1_schedule() -> List[ScheduleEntry]:
    return [_tutorial_entry()]

def get_b2_schedule() -> List[ScheduleEntry]:
    return [_tutorial_entry()]

def get_c1_schedule() -> List[ScheduleEntry]:
    return [_tutorial_entry()]

def load_level_schedules() -> Dict[str, List[ScheduleEntry]]:
    return {
        "A1": get_a1_schedule(),
        "A2": get_a2_schedule(),
        "B1": get_b1_schedule(),
        "B2": get_b2_schedule(),
        "C1": get_c1_schedule(),
    }

def get_level_schedules() -> Dict[str, List[ScheduleEntry]]:
    return load_level_schedules()
