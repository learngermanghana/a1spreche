from datetime import datetime, timedelta, timezone

from src.auth import _SessionStore


class FrozenDateTime:
    current = datetime(2023, 1, 1, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls.current


def test_prune_removes_expired_mappings(monkeypatch):
    FrozenDateTime.current = datetime(2023, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr("src.auth.datetime", FrozenDateTime)
    store = _SessionStore(ttl=60)

    store.set("old", "old")
    FrozenDateTime.current += timedelta(seconds=61)

    assert store.get("old") is None


def test_prune_keeps_active_mappings(monkeypatch):
    FrozenDateTime.current = datetime(2023, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr("src.auth.datetime", FrozenDateTime)
    store = _SessionStore(ttl=60)

    store.set("active", "active")
    FrozenDateTime.current += timedelta(seconds=30)

    assert store.get("active") == "active"
