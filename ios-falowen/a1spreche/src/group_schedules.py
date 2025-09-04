"""Shared group class schedule loader."""
from __future__ import annotations

from typing import Dict, Any


def load_group_schedules() -> Dict[str, Dict[str, Any]]:
    """Return group schedule configuration.

    Centralised so both dashboard and calendar use the same data.
    """
    return {
        "A1 Munich Klasse": {
            "days": ["Monday", "Tuesday", "Wednesday"],
            "time": "6:00pm–7:00pm",
            "start_date": "2025-07-08",
            "end_date": "2025-09-02",
            "doc_url": "https://drive.google.com/file/d/1en_YG8up4C4r36v4r7E714ARcZyvNFD6/view?usp=sharing",
        },
        "A1 Berlin Klasse": {
            "days": ["Monday", "Tuesday", "Wednesday"],
            "time": "Mon/Tues: 11:00am–12:00pm, Wed: 2:00pm–3:00pm",
            "start_date": "2025-09-01",
            "end_date": "2025-10-27",
            "doc_url": "https://drive.google.com/file/d/1piTjRO9M22aFavNmXDAAGI7jvzh10jOD/view?usp=sharing",
        },
        "A1 Koln Klasse": {
            "days": ["Thursday", "Friday", "Saturday"],
            "time": "Thu/Fri: 6:00pm–7:00pm, Sat: 8:00am–9:00am",
            "start_date": "2025-08-15",
            "end_date": "2025-10-11",
            "doc_url": "https://drive.google.com/file/d/1d1Ord557jGRn5NxYsmCJVmwUn1HtrqI3/view?usp=sharing",
        },
        "A2 Munich Klasse": {
            "days": ["Monday", "Tuesday", "Wednesday"],
            "time": "7:30pm–9:00pm",
            "start_date": "2025-06-24",
            "end_date": "2025-08-26",
            "doc_url": "https://drive.google.com/file/d/1Zr3iN6hkAnuoEBvRELuSDlT7kHY8s2LP/view?usp=sharing",
        },
        "A2 Berlin Klasse": {
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time": "Mon–Wed: 11:00am–12:00pm, Thu/Fri: 11:00am–12:00pm, Wed: 2:00pm–3:00pm",
            "start_date": "",
            "end_date": "",
            "doc_url": "",
        },
        "A2 Koln Klasse": {
            "days": ["Wednesday", "Thursday", "Friday"],
            "time": "11:00am–12:00pm",
            "start_date": "2025-08-06",
            "end_date": "2025-10-08",
            "doc_url": "https://drive.google.com/file/d/19cptfdlmBDYe9o84b8ZCwujmxuMCKXAD/view?usp=sharing",
        },
        "B1 Munich Klasse": {
            "days": ["Thursday", "Friday"],
            "time": "7:30pm–9:00pm",
            "start_date": "2025-08-07",
            "end_date": "2025-11-07",
            "doc_url": "https://drive.google.com/file/d/1CaLw9RO6H8JOr5HmwWOZA2O7T-bVByi7/view?usp=sharing",
        },
        "B2 Munich Klasse": {
            "days": ["Friday", "Saturday"],
            "time": "Fri: 2pm-3:30pm, Sat: 9:30am-10am",
            "start_date": "2025-08-08",
            "end_date": "2025-10-08",
            "doc_url": "https://drive.google.com/file/d/1gn6vYBbRyHSvKgqvpj5rr8OfUOYRL09W/view?usp=sharing",
        },
    }
