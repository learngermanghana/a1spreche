from src import attendance_utils


def test_load_attendance_records_counts_sessions(monkeypatch):
    class DummySnap:
        def __init__(self, doc_id, attendees):
            self.id = doc_id
            self._attendees = attendees

        def to_dict(self):
            return {"attendees": self._attendees}

    class DummySessions:
        def stream(self):
            return [
                DummySnap("s1", {"abc": 1}),
                DummySnap("s2", {"xyz": 1}),
                DummySnap("s3", [{"code": "abc"}]),
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

    monkeypatch.setattr(attendance_utils, "db", DummyDB())
    records, count, hours = attendance_utils.load_attendance_records("abc", "C1")
    assert count == 2
    assert hours == 2.0
    assert records[0]["session"] == "s1" and records[0]["present"] is True
    assert records[1]["session"] == "s2" and records[1]["present"] is False


def test_load_attendance_records_handles_error(monkeypatch):
    class DummyDB:
        def collection(self, name):
            raise RuntimeError("boom")

    monkeypatch.setattr(attendance_utils, "db", DummyDB())
    records, count, hours = attendance_utils.load_attendance_records("abc", "C1")
    assert records == []
    assert count == 0
    assert hours == 0.0

