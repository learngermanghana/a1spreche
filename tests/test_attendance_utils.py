from src import attendance_utils


def test_load_attendance_records_counts_sessions(monkeypatch):
    class DummySnap:
        def __init__(self, doc_id, attendees, label):
            self.id = doc_id
            self._attendees = attendees
            self._label = label

        def to_dict(self):
            return {"attendees": self._attendees, "label": self._label}

    class DummySessions:
        def stream(self):
            return [
                DummySnap("s1", {"abc": 1}, "Woche 1: Hallo"),
                DummySnap("s2", {"xyz": 1}, "Woche 2: Tschuess"),
                DummySnap("s3", [{"code": "abc"}], "Woche 3: Wiedersehen"),
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
    assert records[0] == {"session": "Hallo", "present": True}
    assert records[1] == {"session": "Tschuess", "present": False}


def test_load_attendance_records_root_attendees(monkeypatch):
    class DummySnap:
        def __init__(self, doc_id, data):
            self.id = doc_id
            self._data = data

        def to_dict(self):
            d = dict(self._data)
            d["label"] = "Woche 1: Hallo"
            return d

    class DummySessions:
        def stream(self):
            return [
                DummySnap("s1", {"abc": 1, "xyz": 1, "date": "2024-01-01"})
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
    assert count == 1
    assert hours == 1.0
    assert records == [{"session": "Hallo", "present": True}]

    # Metadata fields like ``date`` should not be treated as student codes
    records2, count2, hours2 = attendance_utils.load_attendance_records("date", "C1")
    assert count2 == 0
    assert hours2 == 0.0
    assert records2 == [{"session": "Hallo", "present": False}]


def test_load_attendance_records_only_student_codes(monkeypatch):
    class DummySnap:
        def __init__(self, doc_id, data, label):
            self.id = doc_id
            self._data = data
            self._label = label

        def to_dict(self):
            d = dict(self._data)
            d["label"] = self._label
            return d

    class DummySessions:
        def stream(self):
            return [
                DummySnap("s1", {"abc": 1}, "Woche 1: Hallo"),
                DummySnap("s2", {"xyz": 1}, "Woche 2: Tschuess"),
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
    assert count == 1
    assert hours == 1.0
    assert records == [
        {"session": "Hallo", "present": True},
        {"session": "Tschuess", "present": False},
    ]


def test_load_attendance_records_dict_attendee(monkeypatch):
    class DummySnap:
        def __init__(self, doc_id, data):
            self.id = doc_id
            self._data = data

        def to_dict(self):
            d = dict(self._data)
            d["label"] = "Woche 1: Hallo"
            return d

    class DummySessions:
        def stream(self):
            return [
                DummySnap(
                    "s1",
                    {
                        "felixa2": {
                            "present": True,
                            "name": "Felix Asadu (Tutor)",
                        }
                    },
                )
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
    records, count, hours = attendance_utils.load_attendance_records("felixa2", "C1")
    assert count == 1
    assert hours == 1.0
    assert records == [{"session": "Hallo", "present": True}]


def test_load_attendance_records_dict_attendee_with_hours(monkeypatch):
    class DummySnap:
        def __init__(self, doc_id, data):
            self.id = doc_id
            self._data = data

        def to_dict(self):
            d = dict(self._data)
            d["label"] = "Woche 1: Hallo"
            return d

    class DummySessions:
        def stream(self):
            return [
                DummySnap(
                    "s1",
                    {
                        "felixa2": {
                            "present": True,
                            "hours": 1.5,
                            "name": "Felix Asadu (Tutor)",
                        }
                    },
                )
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
    records, count, hours = attendance_utils.load_attendance_records("felixa2", "C1")
    assert count == 1
    assert abs(hours - 1.5) < 1e-6
    assert records == [{"session": "Hallo", "present": True}]


def test_load_attendance_records_handles_error(monkeypatch):
    class DummyDB:
        def collection(self, name):
            raise RuntimeError("boom")

    monkeypatch.setattr(attendance_utils, "db", DummyDB())
    records, count, hours = attendance_utils.load_attendance_records("abc", "C1")
    assert records == []
    assert count == 0
    assert hours == 0.0

