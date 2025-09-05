from src import firestore_utils
from src.firestore_utils import (
    _extract_level_and_lesson,
    save_question,
    save_response,
)


def test_extract_level_and_lesson_with_prefix():
    level, lesson = _extract_level_and_lesson("draft_B2_day5_ch3")
    assert level == "B2"
    assert lesson == "B2_day5_ch3"


def test_extract_level_and_lesson_without_prefix():
    level, lesson = _extract_level_and_lesson("C1_day2_ch1")
    assert level == "C1"
    assert lesson == "C1_day2_ch1"


def test_save_question_returns_none_without_db(monkeypatch):
    monkeypatch.setattr(firestore_utils, "db", None, raising=False)
    assert save_question("code", "hi") is None


def test_save_response_stores_responder_code(monkeypatch):
    class DummyRef:
        def __init__(self):
            self.payload = None

        def set(self, payload, merge=True):
            self.payload = payload

    class DummyDB:
        def __init__(self):
            self.ref = DummyRef()

        def collection(self, *args, **kwargs):
            return self

        def document(self, *args, **kwargs):
            return self.ref

    dummy_db = DummyDB()
    monkeypatch.setattr(firestore_utils, "db", dummy_db)
    monkeypatch.setattr(firestore_utils.firestore, "ArrayUnion", lambda x: x)
    save_response("id", "hello", "XYZ")
    resp = dummy_db.ref.payload["responses"][0]
    assert resp["responder_code"] == "XYZ"
    assert resp["text"] == "hello"
