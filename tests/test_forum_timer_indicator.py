from datetime import datetime, timedelta, timezone

from src.forum_timer import build_forum_timer_indicator, to_datetime_any


def test_to_datetime_any_handles_naive_datetime():
    naive = datetime(2024, 1, 1, 12, 0, 0)
    parsed = to_datetime_any(naive)
    assert parsed is not None
    assert parsed.tzinfo == timezone.utc
    assert parsed.hour == 12


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
