from src import firestore_utils
from src.firestore_utils import (
    _extract_level_and_lesson,
    save_response,
    save_ai_response,
    fetch_attendance_summary,
)


def test_extract_level_and_lesson_with_prefix():
    level, lesson = _extract_level_and_lesson("draft_B2_day5_ch3")
    assert level == "B2"
    assert lesson == "B2_day5_ch3"


def test_extract_level_and_lesson_without_prefix():
    level, lesson = _extract_level_and_lesson("C1_day2_ch1")
    assert level == "C1"
    assert lesson == "C1_day2_ch1"
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


def test_save_ai_response_stores_flag(monkeypatch):
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
    monkeypatch.setattr(firestore_utils.firestore, "SERVER_TIMESTAMP", 0, raising=False)
    save_ai_response("id1", "hello there", True)
    assert dummy_db.ref.payload["ai_response_suggestion"] == "hello there"
    assert dummy_db.ref.payload["flagged"] is True


def test_fetch_attendance_summary_counts_sessions(monkeypatch):
    class DummySnap:
        def __init__(self, attendees):
            self._attendees = attendees

        def to_dict(self):
            return {"attendees": self._attendees}

    class DummySessions:
        def stream(self):
            return [
                DummySnap({"abc": 1.5, "xyz": 2}),
                DummySnap({"xyz": 1}),
                DummySnap({"abc": 0.5}),
            ]

    class DummyClass:
        def collection(self, name):
            assert name == "sessions"
            return DummySessions()

    class DummyAttendance:
        def document(self, name):
            assert name == "C1"
            return DummyClass()

    class DummyDB:
        def collection(self, name):
            assert name == "attendance"
            return DummyAttendance()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())
    count, hours = fetch_attendance_summary("abc", "C1")
    assert count == 2
    assert abs(hours - 2.0) < 1e-6


def test_fetch_attendance_summary_root_attendees(monkeypatch):
    class DummySnap:
        def __init__(self, data):
            self._data = data

        def to_dict(self):
            return self._data

    class DummySessions:
        def stream(self):
            return [
                DummySnap({"abc": True, "xyz": True}),
                DummySnap({"abc": 2, "date": "2024-01-01"}),
            ]

    class DummyClass:
        def collection(self, name):
            assert name == "sessions"
            return DummySessions()

    class DummyAttendance:
        def document(self, name):
            assert name == "C1"
            return DummyClass()

    class DummyDB:
        def collection(self, name):
            assert name == "attendance"
            return DummyAttendance()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())
    count, hours = fetch_attendance_summary("abc", "C1")
    assert count == 2
    assert abs(hours - 3.0) < 1e-6
