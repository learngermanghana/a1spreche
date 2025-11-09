from types import SimpleNamespace

from src.grammar_helper_persistence import (
    clear_grammar_helper_state,
    load_grammar_helper_state,
    persist_grammar_helper_state,
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


def test_persist_grammar_helper_state_includes_meta(monkeypatch):
    """Persisting chat state should include level metadata for tutors."""

    doc = _StubDoc()
    messages = [{"role": "user", "content": "Hallo"}]

    monkeypatch.setattr(
        "src.grammar_helper_persistence.firestore",
        SimpleNamespace(SERVER_TIMESTAMP="ts"),
    )

    result = persist_grammar_helper_state(
        doc,
        messages=messages,
        level="B1",
        student_code="stu-42",
    )

    assert result is True
    assert doc.merge_flags == [True]
    assert len(doc.saved_payloads) == 1

    payload = doc.saved_payloads[0]
    assert payload["chats"]["grammar_helper"] == messages

    meta = payload["grammar_helper_meta"]
    assert meta["level"] == "B1"
    assert meta["student_code"] == "stu-42"
    assert meta["message_count"] == 1
    assert meta["updated_at"] == "ts"


def test_load_grammar_helper_state_returns_messages(monkeypatch):
    """Loading state should return stored messages and metadata."""

    stored = {
        "chats": {
            "grammar_helper": [
                {"role": "user", "content": "Hallo"},
                {"role": "assistant", "content": "Guten Tag"},
            ]
        },
        "grammar_helper_meta": {"level": "B1"},
    }
    doc = _StubDoc(stored)
    db = _StubDB(doc)

    doc_ref, messages, meta = load_grammar_helper_state(db, "stu-42")

    assert doc_ref is doc
    assert messages == stored["chats"]["grammar_helper"]
    assert meta == stored["grammar_helper_meta"]
    assert db.collection_calls == ["falowen_chats"]


def test_clear_grammar_helper_state_uses_delete_field(monkeypatch):
    """Clearing should issue a merge delete when supported."""

    doc = _StubDoc()

    monkeypatch.setattr(
        "src.grammar_helper_persistence.firestore",
        SimpleNamespace(DELETE_FIELD="__del__"),
    )

    result = clear_grammar_helper_state(doc)

    assert result is True
    assert doc.merge_flags == [True]
    saved = doc.saved_payloads[0]
    assert saved["chats"]["grammar_helper"] == "__del__"
    assert saved["grammar_helper_meta"] == "__del__"

