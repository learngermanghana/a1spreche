from types import SimpleNamespace

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
