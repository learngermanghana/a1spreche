"""Shared group class schedule loader."""
from __future__ import annotations

from typing import Dict, Any


def load_group_schedules() -> Dict[str, Dict[str, Any]]:
    """Return group schedule configuration.

    Centralised so both dashboard and calendar use the same data.
    """
    return {
        "A1 Frankfurt Klasse": {
            "days": ["Thursday", "Friday", "Saturday"],
            "time": "Thu/Fri: 6:00pm–7:00pm, Sat: 8:00am–9:00am",
            "start_date": "2025-10-23",
            "end_date": "2025-12-18",
            "doc_url": "https://drive.google.com/file/d/1BFPE0gvTb7DWPRqdfWhLzbvgwhLbGvRv/view?usp=sharing",
        },
        "A1 Bonn Klasse": {
            "days": ["Monday", "Tuesday", "Wednesday"],
            "time": "11:00am–12:00pm",
            "start_date": "2025-11-10",
            "end_date": "2026-01-13",
            "doc_url": "https://drive.google.com/file/d/13X4LxOTE4yfe4dw_k_ILLdzrbTm54ZEI/view?usp=sharing",
        },
        "A1 Munich Klasse": {
            "days": ["Monday", "Tuesday", "Wednesday"],
            "time": "6:00pm–7:00pm",
            "start_date": "2025-12-03",
            "end_date": "2026-02-09",
            "doc_url": "https://drive.google.com/file/d/1YaML32aP8L0Uk_-fu2HEW1b0Qo4CceDg/view?usp=sharing",
        },
        "A2 Bonn Klasse": {
            "days": ["Tuesday", "Wednesday", "Thursday"],
            "time": "7:30pm–9:00pm",
            "start_date": "2025-11-25",
            "end_date": "2026-02-04",
            "doc_url": "https://drive.google.com/file/d/1dE9cEXY9CC25lAXZuWNvQCFWis6nx0hW/view?usp=sharing",
        },
        "B1 Koln Klasse": {
            "days": ["Thursday", "Friday"],
            "time": "7:30pm–9:00pm",
            "start_date": "2025-11-20",
            "end_date": "2026-02-27",
            "doc_url": "https://drive.google.com/file/d/1sQ1ePNRapuVcih7BnhNNBQrO3SkM9K-O/view?usp=sharing",
        },
        "B2 Munich Klasse": {
            "days": ["Friday", "Saturday"],
            "time": "Fri: 2pm-3:30pm, Sat: 9:30am-10am",
            "start_date": "2025-08-08",
            "end_date": "2025-10-08",
            "doc_url": "https://drive.google.com/file/d/1gn6vYBbRyHSvKgqvpj5rr8OfUOYRL09W/view?usp=sharing",
        },
    }
