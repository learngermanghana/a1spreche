"""Course schedule utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

import streamlit as st

SCHEDULES_PATH = Path(__file__).resolve().parent.parent / "data" / "schedules.json"

REQUIRED_KEYS = {"day", "topic"}


def _validate(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Validate raw schedules data.

    Ensures the top-level structure is a mapping of level names to a list of
    schedule entries. Each entry must contain at least the keys defined in
    ``REQUIRED_KEYS``.
    """
    if not isinstance(data, dict):
        raise ValueError("Schedules data must be a dictionary")

    for level, items in data.items():
        if not isinstance(level, str):
            raise ValueError("Schedule level keys must be strings")
        if not isinstance(items, list):
            raise ValueError(f"Schedule for {level} must be a list")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Each schedule entry for {level} must be a dict")
            missing = REQUIRED_KEYS - item.keys()
            if missing:
                raise ValueError(
                    f"Schedule entry for {level} missing keys: {', '.join(sorted(missing))}"
                )
    return data


@st.cache_data(ttl=86400)
def _load_schedules_cached() -> Dict[str, List[Dict[str, Any]]]:
    """Load schedules from disk and cache the result."""
    with SCHEDULES_PATH.open(encoding="utf-8") as f:
        raw = json.load(f)
    return _validate(raw)


def load_level_schedules() -> Dict[str, List[Dict[str, Any]]]:
    """Return all level schedules, loading them if necessary."""
    if "level_schedules" not in st.session_state:
        st.session_state["level_schedules"] = _load_schedules_cached()
    return st.session_state["level_schedules"]


def get_level_schedules() -> Dict[str, List[Dict[str, Any]]]:
    """Public accessor mirroring existing API."""
    return load_level_schedules()


def _get_schedule(level: str) -> List[Dict[str, Any]]:
    return get_level_schedules().get(level, [])


def get_a1_schedule() -> List[Dict[str, Any]]:
    return _get_schedule("A1")


def get_a2_schedule() -> List[Dict[str, Any]]:
    return _get_schedule("A2")


def get_b1_schedule() -> List[Dict[str, Any]]:
    return _get_schedule("B1")


def get_b2_schedule() -> List[Dict[str, Any]]:
    return _get_schedule("B2")


def get_c1_schedule() -> List[Dict[str, Any]]:
    return _get_schedule("C1")
