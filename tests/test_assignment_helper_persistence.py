"""Tests for the Assignment Helper persistence helpers."""

from types import SimpleNamespace

from src.assignment_helper_persistence import (
    persist_assignment_helper_state,
    record_assignment_helper_thread,
)


class _StubDoc:
    """Minimal Firestore document stub capturing ``set`` payloads."""

    def __init__(self, exists: bool = False) -> None:
        self._exists = exists
        self.saved_payloads = []
        self.merge_flags = []

    def get(self):  # pragma: no cover - trivial shim
        return SimpleNamespace(exists=self._exists)

    def set(self, payload, merge=False):  # pragma: no cover - trivial shim
        self.saved_payloads.append(payload)
        self.merge_flags.append(merge)
        self._exists = True


class _StubDB:
    """Minimal Firestore client stub returning :class:`_StubDoc` instances."""

    def __init__(self, doc: _StubDoc) -> None:
        self._doc = doc
        self.collection_calls = []

    def collection(self, name):  # pragma: no cover - trivial shim
        self.collection_calls.append(name)
        return SimpleNamespace(document=lambda _: self._doc)


def test_persist_assignment_helper_state_includes_thread_metadata(monkeypatch):
    """Persisting chat state should include thread metadata for tutors."""

    doc = _StubDoc()
    messages = [{"role": "user", "content": "Hallo"}]

    result = persist_assignment_helper_state(
        doc,
        messages=messages,
        level="B1",
        thread_id="abc123",
        student_code="stu-42",
    )

    assert result is True
    assert doc.merge_flags == [True]
    assert len(doc.saved_payloads) == 1

    payload = doc.saved_payloads[0]
    assert payload["chats"]["assignment_helper"] == messages

    meta = payload["assignment_helper_meta"]
    assert meta["thread_id"] == "abc123"
    assert meta["student_code"] == "stu-42"
    assert meta["level"] == "B1"
    assert meta["message_count"] == 1


def test_record_assignment_helper_thread_updates_summary(monkeypatch):
    """Recording a thread should update the summary document with metadata."""

    doc = _StubDoc()
    db = _StubDB(doc)

    monkeypatch.setattr(
        "src.assignment_helper_persistence.firestore",
        SimpleNamespace(SERVER_TIMESTAMP="ts"),
    )

    result = record_assignment_helper_thread(
        db,
        thread_id="thread-1",
        student_code="stu-42",
        level="B2",
        message_count=3,
    )

    assert result is True
    assert db.collection_calls == ["assignment_helper_threads"]
    assert doc.merge_flags == [True]

    saved = doc.saved_payloads[0]
    assert saved["thread_id"] == "thread-1"
    assert saved["student_code"] == "stu-42"
    assert saved["level"] == "B2"
    assert saved["message_count"] == 3
    assert saved["updated_at"] == "ts"
    assert saved["created_at"] == "ts"


def test_record_assignment_helper_thread_requires_identifier(monkeypatch):
    """Recording a thread without a valid identifier should be ignored."""

    doc = _StubDoc()
    db = _StubDB(doc)

    assert record_assignment_helper_thread(db, thread_id="", student_code="x") is False
    assert doc.saved_payloads == []
