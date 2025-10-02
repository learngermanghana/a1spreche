from datetime import datetime, timedelta, timezone

import pytest

from src import stats
from src.vocab.scheduler import VocabScheduleManager


class StubDoc:
    def __init__(self, store, student):
        self._store = store
        self._student = student
        self.exists = student in store

    def to_dict(self):
        if self._student not in self._store:
            return {}
        return dict(self._store[self._student])


class StubDocRef:
    def __init__(self, store, student):
        self._store = store
        self._student = student
        self.saved_payloads = []

    def get(self):
        return StubDoc(self._store, self._student)

    def set(self, payload, merge=True):
        self.saved_payloads.append(payload)
        existing = self._store.get(self._student, {}) if merge else {}
        updated = _deep_merge(existing, payload) if merge else dict(payload)
        self._store[self._student] = updated


class StubCollection:
    def __init__(self, store):
        self._store = store

    def document(self, student):
        return StubDocRef(self._store, student)


class StubDB:
    def __init__(self):
        self._collections = {}

    def collection(self, name):
        coll_store = self._collections.setdefault(name, {})
        return StubCollection(coll_store)


def _deep_merge(target, update):
    result = dict(target)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@pytest.fixture
def fixed_now():
    return datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)


def test_record_session_updates_intervals(fixed_now):
    manager = VocabScheduleManager("stu", schedule={}, now=fixed_now)

    first = manager.record_session(["Hund"], [])
    hund_state = first["Hund"]
    assert hund_state["interval"] == 1
    assert hund_state["repetitions"] == 1
    assert hund_state["last_result"] == "correct"
    next_due = datetime.fromisoformat(hund_state["next_due"])
    assert next_due.date() == (fixed_now + timedelta(days=1)).date()

    manager2 = VocabScheduleManager(
        "stu",
        schedule={"Hund": hund_state},
        now=fixed_now + timedelta(days=2),
    )
    second = manager2.record_session(["Hund"], [])
    hund_state2 = second["Hund"]
    assert hund_state2["interval"] >= 3
    assert hund_state2["repetitions"] == 2

    manager3 = VocabScheduleManager(
        "stu",
        schedule={"Hund": hund_state2},
        now=fixed_now + timedelta(days=5),
    )
    third = manager3.record_session(["Hund"], ["Hund"])
    hund_state3 = third["Hund"]
    assert hund_state3["interval"] == 1
    assert hund_state3["repetitions"] == 0
    assert hund_state3["last_result"] == "incorrect"


def test_snooze_and_reset_cards(fixed_now):
    existing = {
        "Hund": {
            "ease": 2.5,
            "interval": 2,
            "repetitions": 1,
            "last_review": fixed_now.isoformat(),
            "next_due": (fixed_now + timedelta(days=1)).isoformat(),
            "last_result": "correct",
        }
    }
    manager = VocabScheduleManager("stu", schedule=existing, now=fixed_now)

    snoozed = manager.snooze_cards(["Hund"], days=3)
    new_due = datetime.fromisoformat(snoozed["Hund"]["next_due"])
    assert new_due.date() == (fixed_now + timedelta(days=4)).date()

    resets = manager.reset_cards(["Hund"])
    assert resets["Hund"] is None
    assert "Hund" not in manager.known_words


def test_save_vocab_attempt_persists_schedule(fixed_now):
    stub_db = StubDB()
    stats.db = stub_db  # type: ignore[attr-defined]

    student = "stu"
    schedule_update = {
        "Hund": {
            "ease": 2.6,
            "interval": 3,
            "repetitions": 2,
            "last_review": fixed_now.isoformat(),
            "next_due": (fixed_now + timedelta(days=3)).isoformat(),
            "last_result": "correct",
        }
    }

    stats.save_vocab_attempt(
        student_code=student,
        level="A1",
        total=2,
        correct=1,
        practiced_words=["Hund", "Katze"],
        session_id="sess-1",
        incorrect_words=["Katze"],
        schedule_updates=schedule_update,
    )

    stored = stub_db.collection("vocab_stats")._store[student]
    assert stored["history"]
    assert stored["schedule"]["Hund"]["interval"] == 3
    assert stored["incorrect_words"] == ["Katze"]

    stats.db = None  # type: ignore[attr-defined]
