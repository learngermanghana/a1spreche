from types import SimpleNamespace

from src.topic_coach_persistence import (
    TOPIC_COACH_CHAT_KEY,
    TOPIC_COACH_META_FIELD,
    get_topic_coach_doc,
    load_topic_coach_state,
    persist_topic_coach_state,
)


class FakeSnapshot:
    def __init__(self, data, exists=True):
        self._data = data
        self.exists = exists

    def to_dict(self):
        return self._data


def _deep_merge(target, payload):
    for key, value in payload.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


class FakeDocRef:
    def __init__(self, data=None, doc_id="doc1"):
        self._data = data or {}
        self.id = doc_id
        self.set_calls = []

    def get(self):
        return FakeSnapshot(self._data, exists=True)

    def set(self, payload, merge=True):
        self.set_calls.append((payload, merge))
        if merge:
            _deep_merge(self._data, payload)
        else:
            self._data = payload


class FakeDB:
    def __init__(self, doc):
        self._doc = doc

    def collection(self, name):
        assert name == "falowen_chats"
        return self

    def document(self, student_code):
        doc = getattr(self, "_doc", None)
        if isinstance(doc, dict):
            return FakeDocRef(doc, doc_id=student_code)
        return doc


def test_load_topic_coach_state_returns_messages_and_meta():
    stored = {
        "chats": {TOPIC_COACH_CHAT_KEY: [{"role": "assistant", "content": "Hallo"}]},
        TOPIC_COACH_META_FIELD: {"qcount": 3, "finalized": True},
    }
    db = FakeDB(stored)

    doc_ref, messages, meta = load_topic_coach_state(db, "stu1")

    assert doc_ref is not None
    assert messages == stored["chats"][TOPIC_COACH_CHAT_KEY]
    assert meta == stored[TOPIC_COACH_META_FIELD]


def test_persist_topic_coach_state_writes_payload():
    base = {
        "chats": {},
        TOPIC_COACH_META_FIELD: {"qcount": 0, "finalized": False},
    }
    doc_ref = FakeDocRef(base, doc_id="stu2")

    saved = persist_topic_coach_state(
        doc_ref,
        messages=[{"role": "user", "content": "Hi"}],
        qcount=2,
        finalized=True,
    )

    assert saved is True
    payload, merge_flag = doc_ref.set_calls[-1]
    assert merge_flag is True
    assert payload["chats"][TOPIC_COACH_CHAT_KEY] == [{"role": "user", "content": "Hi"}]
    assert payload[TOPIC_COACH_META_FIELD] == {"qcount": 2, "finalized": True}
    assert doc_ref._data["chats"][TOPIC_COACH_CHAT_KEY]
    assert doc_ref._data[TOPIC_COACH_META_FIELD]["finalized"] is True


def test_topic_coach_state_round_trip():
    storage = {
        "chats": {},
        TOPIC_COACH_META_FIELD: {"qcount": 0, "finalized": False},
    }
    doc_ref = FakeDocRef(storage, doc_id="stu3")
    db = SimpleNamespace(collection=lambda name: SimpleNamespace(document=lambda code: doc_ref))

    persisted = persist_topic_coach_state(
        doc_ref,
        messages=[{"role": "assistant", "content": "Start"}],
        qcount=1,
        finalized=False,
    )
    assert persisted is True

    loaded_doc, messages, meta = load_topic_coach_state(db, "stu3")
    assert loaded_doc is doc_ref
    assert messages == [{"role": "assistant", "content": "Start"}]
    assert meta == {"qcount": 1, "finalized": False}


def test_persist_topic_coach_state_requires_document():
    assert persist_topic_coach_state(None, messages=[], qcount=0, finalized=False) is False


def test_get_topic_coach_doc_handles_missing_db():
    assert get_topic_coach_doc(None, "stu4") is None
    assert get_topic_coach_doc(SimpleNamespace(collection=lambda name: None), "") is None
