from datetime import datetime, timedelta, timezone

from src import firestore_utils


class DummyDoc:
    def __init__(self):
        self.set_payloads = []
        self.deleted = 0

    def set(self, payload):
        self.set_payloads.append(payload)

    def delete(self):
        self.deleted += 1


class DummySnapshot:
    def __init__(self, sid, data):
        self.id = sid
        self._data = data

    def to_dict(self):
        return dict(self._data)


def test_set_typing_indicator_updates_and_clears(monkeypatch):
    doc = DummyDoc()
    monkeypatch.setattr(
        firestore_utils,
        "_typing_doc_ref",
        lambda *args, **kwargs: doc,
    )

    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert firestore_utils.set_typing_indicator(
        "A1",
        "Class-1",
        "post1",
        "stu",
        "Student",
        is_typing=True,
        now=now,
    )
    assert doc.set_payloads[-1]["student_name"] == "Student"
    assert doc.set_payloads[-1]["last_seen"].tzinfo is timezone.utc

    assert firestore_utils.set_typing_indicator(
        "A1",
        "Class-1",
        "post1",
        "stu",
        "Student",
        is_typing=False,
    )
    assert doc.deleted == 1


def test_set_typing_indicator_handles_failures(monkeypatch):
    class FailingDoc:
        def set(self, payload):
            raise RuntimeError("boom")

        def delete(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        firestore_utils,
        "_typing_doc_ref",
        lambda *args, **kwargs: FailingDoc(),
    )

    assert not firestore_utils.set_typing_indicator(
        "A1",
        "C",
        "q",
        "stu",
        "Name",
        is_typing=True,
    )
    assert not firestore_utils.set_typing_indicator(
        "A1",
        "C",
        "q",
        "stu",
        "Name",
        is_typing=False,
    )


def test_fetch_active_typists_filters_expired(monkeypatch):
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    recent = now - timedelta(seconds=5)
    stale = now - timedelta(seconds=45)

    class DummyCollection:
        def stream(self):
            return [
                DummySnapshot("abc", {"student_name": "Alice", "last_seen": recent}),
                DummySnapshot("xyz", {"student_name": "Bob", "last_seen": stale}),
                DummySnapshot("raw", {"student_name": "Raw", "last_seen": 0}),
            ]

    monkeypatch.setattr(
        firestore_utils,
        "_typing_collection",
        lambda *args, **kwargs: DummyCollection(),
    )

    active = firestore_utils.fetch_active_typists(
        "A1",
        "Class-1",
        "post1",
        now=now,
        ttl_seconds=10,
    )

    assert [entry["student_code"] for entry in active] == ["abc"]
    assert active[0]["last_seen"] == recent


def test_fetch_active_typists_handles_stream_failure(monkeypatch):
    class BrokenCollection:
        def stream(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        firestore_utils,
        "_typing_collection",
        lambda *args, **kwargs: BrokenCollection(),
    )

    assert firestore_utils.fetch_active_typists("A1", "C", "post1") == []


def test_fetch_active_typists_handles_missing_collection(monkeypatch):
    monkeypatch.setattr(
        firestore_utils,
        "_typing_collection",
        lambda *args, **kwargs: None,
    )
    assert firestore_utils.fetch_active_typists("A1", "C", "post1") == []
