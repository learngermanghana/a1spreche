from types import SimpleNamespace

from src.assignment_helper_persistence import (
    clear_assignment_helper_state,
    load_assignment_helper_state,
    persist_assignment_helper_state,
    record_assignment_helper_thread,
)


class _StubDoc:
    """Minimal Firestore document stub capturing ``set`` payloads."""

    def __init__(self, data=None) -> None:
        self._data = data
        self.saved_payloads = []
        self.merge_flags = []
        self.deleted = False

    def get(self):  # pragma: no cover - trivial shim
        data = self._data

        def _to_dict():
            return data

        exists = data is not None
        return SimpleNamespace(exists=exists, to_dict=_to_dict)

    def set(self, payload, merge=False):  # pragma: no cover - trivial shim
        self.saved_payloads.append(payload)
        self.merge_flags.append(merge)
        if merge and isinstance(self._data, dict):
            combined = dict(self._data)
            combined.update(payload)
            self._data = combined
        else:
            self._data = payload

    def delete(self):  # pragma: no cover - trivial shim
        self.deleted = True


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

    monkeypatch.setattr(
        "src.assignment_helper_persistence.firestore",
        SimpleNamespace(SERVER_TIMESTAMP="ts"),
    )

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
    assert meta["updated_at"] == "ts"


def test_load_assignment_helper_state_returns_messages():
    """Loading state should return stored messages and metadata."""

    stored = {
        "chats": {
            "assignment_helper": [
                {"role": "user", "content": "Hallo"},
                {"role": "assistant", "content": "Guten Tag"},
            ]
        },
        "assignment_helper_meta": {"level": "B1"},
    }
    doc = _StubDoc(stored)
    db = _StubDB(doc)

    doc_ref, messages, meta = load_assignment_helper_state(db, "stu-42")

    assert doc_ref is doc
    assert messages == stored["chats"]["assignment_helper"]
    assert meta == stored["assignment_helper_meta"]
    assert db.collection_calls == ["falowen_chats"]


def test_clear_assignment_helper_state_uses_delete_field(monkeypatch):
    """Clearing should issue a merge delete when supported."""

    doc = _StubDoc()

    monkeypatch.setattr(
        "src.assignment_helper_persistence.firestore",
        SimpleNamespace(DELETE_FIELD="__del__"),
    )

    result = clear_assignment_helper_state(doc)

    assert result is True
    assert doc.merge_flags == [True]
    saved = doc.saved_payloads[0]
    assert saved["chats"]["assignment_helper"] == "__del__"
    assert saved["assignment_helper_meta"] == "__del__"


def test_clear_assignment_helper_state_without_delete_field(monkeypatch):
    """Clearing without Firestore helpers should blank the stored transcript."""

    stored = {
        "chats": {"assignment_helper": [{"role": "user", "content": "Hallo"}]},
        "assignment_helper_meta": {"level": "B1"},
    }
    doc = _StubDoc(stored)

    monkeypatch.setattr(
        "src.assignment_helper_persistence.firestore",
        SimpleNamespace(),
    )

    result = clear_assignment_helper_state(doc)

    assert result is True
    assert doc.merge_flags == [True]
    saved = doc.saved_payloads[0]
    assert saved["chats"]["assignment_helper"] == []
    assert saved["assignment_helper_meta"] == {}


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

    monkeypatch.setattr(
        "src.assignment_helper_persistence.firestore",
        SimpleNamespace(),
    )

    assert record_assignment_helper_thread(db, thread_id="", student_code="x") is False
    assert doc.saved_payloads == []
