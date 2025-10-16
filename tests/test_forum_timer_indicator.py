from datetime import datetime, timedelta, timezone

from src.forum_timer import (
    build_forum_reply_indicator_text,
    build_forum_timer_indicator,
    to_datetime_any,
)


def test_to_datetime_any_handles_naive_datetime():
    naive = datetime(2024, 1, 1, 12, 0, 0)
    parsed = to_datetime_any(naive)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 12


def test_to_datetime_any_handles_iso_z_string():
    iso_value = "2024-06-01T10:15:30Z"
    parsed = to_datetime_any(iso_value)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.year == 2024
    assert parsed.month == 6
    assert parsed.day == 1
    assert parsed.hour == 10
    assert parsed.minute == 15
    assert parsed.second == 30


def test_build_forum_timer_indicator_future_minutes():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    expires = now + timedelta(minutes=12)
    info = build_forum_timer_indicator(expires, now=now)
    assert info["status"] == "open"
    assert info["minutes"] == 12
    assert info["label"] == "⏳ 12 minutes left"


def test_build_forum_timer_indicator_closed():
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    expires = now - timedelta(minutes=1)
    info = build_forum_timer_indicator(expires, now=now)
    assert info["status"] == "closed"
    assert info["minutes"] == 0
    assert info["label"] == "Forum closed"


def test_build_forum_reply_indicator_text_mirrors_open_label():
    info = {
        "status": "open",
        "label": "⏳ 7 minutes left",
        "minutes": 7,
    }
    assert build_forum_reply_indicator_text(info) == "⏳ 7 minutes left"


def test_build_forum_reply_indicator_text_handles_closed_state():
    info = {
        "status": "closed",
        "label": "Forum closed",
        "minutes": 0,
    }
    assert build_forum_reply_indicator_text(info) == "Forum closed"


def test_build_forum_reply_indicator_text_empty_when_no_timer():
    assert build_forum_reply_indicator_text({"status": "none", "label": ""}) == ""
