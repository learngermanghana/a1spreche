from types import SimpleNamespace

import pytest

from src.falowen import chat_core


class FakeSnapshot:
    def __init__(self, data):
        self._data = data
        self.exists = True

    def to_dict(self):
        return self._data


class FakeDocRef:
    def __init__(self, data):
        self._data = data
        self.set_calls = []

    def get(self):
        return FakeSnapshot(self._data)

    def set(self, payload, merge=False):
        self.set_calls.append((payload, merge))


class FakeDB:
    def __init__(self, data):
        self._data = data
        self.doc_ref = FakeDocRef(data)

    def collection(self, name):
        assert name == "falowen_chats"
        return self

    def document(self, student_code):
        self.doc_ref.student_code = student_code
        return self.doc_ref


@pytest.fixture
def multiple_chat_doc_data():
    populated_key = "Chat Mode_A1_custom_f00dbabe"
    sparse_key = "Chat Mode_A1_custom_00c0ffee"
    extra_key = "Chat Mode_B1_custom_deadbeef"
    doc_data = {
        "chats": {
            sparse_key: [
                {"role": "assistant", "content": "Hallo"},
            ],
            populated_key: [
                {"role": "assistant", "content": "Hallo"},
                {"role": "user", "content": "Guten Tag"},
                {"role": "assistant", "content": "Wie geht's?"},
            ],
            extra_key: [
                {"role": "assistant", "content": "Should not match"},
            ],
        }
    }
    return doc_data, populated_key, sparse_key


def test_prepare_chat_session_reuses_existing_chat(monkeypatch):
    st = SimpleNamespace(session_state={})
    st.session_state["student_code"] = "stu1"
    monkeypatch.setattr(chat_core, "st", st)
    monkeypatch.setattr(chat_core, "load_chat_draft_from_db", lambda *args, **kwargs: "")

    existing_key = "Chat Mode_A1_custom_deadbeef"
    stored_messages = [{"role": "assistant", "content": "Hallo"}]
    doc_data = {"chats": {existing_key: stored_messages}}
    fake_db = FakeDB(doc_data)

    session = chat_core.prepare_chat_session(
        db=fake_db,
        student_code="stu1",
        mode="Chat Mode",
        level="A1",
        teil=None,
    )

    assert session.conv_key == existing_key
    assert st.session_state["falowen_messages"] == stored_messages
    assert set(doc_data["chats"].keys()) == {existing_key}
    assert fake_db.doc_ref.set_calls
    payload, merge = fake_db.doc_ref.set_calls[-1]
    assert payload == {"current_conv": {"Chat Mode_A1_custom": existing_key}}
    assert merge is True


def test_prepare_chat_session_prefers_most_populated_history(
    monkeypatch, multiple_chat_doc_data
):
    doc_data, populated_key, _ = multiple_chat_doc_data
    st = SimpleNamespace(session_state={})
    st.session_state["student_code"] = "stu2"
    monkeypatch.setattr(chat_core, "st", st)
    monkeypatch.setattr(chat_core, "load_chat_draft_from_db", lambda *args, **kwargs: "")

    fake_db = FakeDB(doc_data)

    session = chat_core.prepare_chat_session(
        db=fake_db,
        student_code="stu2",
        mode="Chat Mode",
        level="A1",
        teil=None,
    )

    assert session.conv_key == populated_key
    assert st.session_state["falowen_messages"] == doc_data["chats"][populated_key]
    payload, merge = fake_db.doc_ref.set_calls[-1]
    assert payload == {"current_conv": {"Chat Mode_A1_custom": populated_key}}
    assert merge is True


def test_prepare_chat_session_respects_existing_pointers(
    monkeypatch, multiple_chat_doc_data
):
    base_doc_data, _, sparse_key = multiple_chat_doc_data
    monkeypatch.setattr(chat_core, "load_chat_draft_from_db", lambda *args, **kwargs: "")

    doc_with_current = {
        "current_conv": {"Chat Mode_A1_custom": sparse_key},
        "drafts": {sparse_key: {"draft": ""}},
        "chats": base_doc_data["chats"],
    }
    st_current = SimpleNamespace(session_state={})
    st_current.session_state["student_code"] = "stu3"
    monkeypatch.setattr(chat_core, "st", st_current)

    fake_db_current = FakeDB(doc_with_current)

    session_current = chat_core.prepare_chat_session(
        db=fake_db_current,
        student_code="stu3",
        mode="Chat Mode",
        level="A1",
        teil=None,
    )

    assert session_current.conv_key == sparse_key
    assert st_current.session_state["falowen_messages"] == base_doc_data["chats"][sparse_key]
    payload, merge = fake_db_current.doc_ref.set_calls[-1]
    assert payload == {"current_conv": {"Chat Mode_A1_custom": sparse_key}}
    assert merge is True

    doc_with_draft = {
        "drafts": {sparse_key: {"draft": ""}},
        "chats": base_doc_data["chats"],
    }
    st_draft = SimpleNamespace(session_state={})
    st_draft.session_state["student_code"] = "stu4"
    monkeypatch.setattr(chat_core, "st", st_draft)

    fake_db_draft = FakeDB(doc_with_draft)

    session_draft = chat_core.prepare_chat_session(
        db=fake_db_draft,
        student_code="stu4",
        mode="Chat Mode",
        level="A1",
        teil=None,
    )

    assert session_draft.conv_key == sparse_key
    assert st_draft.session_state["falowen_messages"] == base_doc_data["chats"][sparse_key]
    payload, merge = fake_db_draft.doc_ref.set_calls[-1]
    assert payload == {"current_conv": {"Chat Mode_A1_custom": sparse_key}}
    assert merge is True
