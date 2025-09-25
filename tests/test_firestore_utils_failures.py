import logging

from src import firestore_utils


def test_save_draft_to_db_logs_warning_on_failure(monkeypatch, caplog):
    class DummyRef:
        def set(self, *args, **kwargs):
            raise RuntimeError("boom")

    def dummy_ref(level, lesson_key, code):
        return DummyRef()

    monkeypatch.setattr(firestore_utils, "db", object())
    monkeypatch.setattr(firestore_utils, "_draft_doc_ref", dummy_ref)

    with caplog.at_level(logging.WARNING):
        result = firestore_utils.save_draft_to_db("code", "draft_X", "text")
    assert result is False
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_save_chat_draft_to_db_logs_warning_on_failure(monkeypatch, caplog):
    class DummyDoc:
        def set(self, *args, **kwargs):
            raise RuntimeError("boom")

    class DummyCollection:
        def document(self, *args, **kwargs):
            return DummyDoc()

    class DummyDB:
        def collection(self, *args, **kwargs):
            return DummyCollection()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.WARNING):
        result = firestore_utils.save_chat_draft_to_db("code", "conv", "hi")
    assert result is False
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_save_chat_draft_to_db_logs_warning_on_failure_when_clearing(monkeypatch, caplog):
    class DummyDoc:
        def set(self, *args, **kwargs):
            raise RuntimeError("boom")

    class DummyCollection:
        def document(self, *args, **kwargs):
            return DummyDoc()

    class DummyDB:
        def collection(self, *args, **kwargs):
            return DummyCollection()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.WARNING):
        result = firestore_utils.save_chat_draft_to_db("code", "conv", "")
    assert result is False
    assert any(record.levelno == logging.WARNING for record in caplog.records)

def test_load_chat_draft_from_db_logs_error_on_failure(monkeypatch, caplog):
    class DummyDB:
        def collection(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.ERROR):
        result = firestore_utils.load_chat_draft_from_db("code", "conv")
    assert result == ""
    assert any(
        "Failed to load chat draft for code/conv" in record.message
        for record in caplog.records
    )


def test_load_draft_meta_from_db_logs_error_on_failure(monkeypatch, caplog):
    class DummyDB:
        def collection(self, *args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.ERROR):
        text, ts = firestore_utils.load_draft_meta_from_db("code", "draft_X")
    assert text == ""
    assert ts is None
    messages = [
        record.message
        for record in caplog.records
        if "Failed to load draft meta" in record.message
    ]
    # three paths attempted: new, compat, legacy
    assert len(messages) == 3
    assert all("code/draft_X" in msg for msg in messages)


def test_save_ai_answer_logs_warning_on_failure(monkeypatch, caplog):
    class DummyRef:
        def set(self, *args, **kwargs):
            raise RuntimeError("boom")

    class DummyDB:
        def collection(self, *args, **kwargs):
            return self

        def document(self, *args, **kwargs):
            return DummyRef()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.WARNING):
        firestore_utils.save_ai_answer("id", "text")
    assert any("Failed to save AI answer" in r.message for r in caplog.records)


def test_save_ai_response_logs_warning_on_failure(monkeypatch, caplog):
    class DummyRef:
        def set(self, *args, **kwargs):
            raise RuntimeError("boom")

    class DummyDB:
        def collection(self, *args, **kwargs):
            return self

        def document(self, *args, **kwargs):
            return DummyRef()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.WARNING):
        firestore_utils.save_ai_response("id", "text")
    assert any("Failed to save AI response" in r.message for r in caplog.records)


def test_save_response_logs_warning_on_failure(monkeypatch, caplog):
    class DummyRef:
        def set(self, *args, **kwargs):
            raise RuntimeError("boom")

    class DummyDB:
        def collection(self, *args, **kwargs):
            return self

        def document(self, *args, **kwargs):
            return DummyRef()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())

    with caplog.at_level(logging.WARNING):
        firestore_utils.save_response("id", "text", "code")
    assert any("Failed to save response" in r.message for r in caplog.records)


def test_fetch_attendance_summary_logs_error(monkeypatch, caplog):
    class DummySessions:
        def stream(self):
            raise RuntimeError("boom")

    class DummyClass:
        def collection(self, name):
            return DummySessions()

    class DummyAttendance:
        def document(self, name):
            return DummyClass()

    class DummyDB:
        def collection(self, name):
            return DummyAttendance()

    monkeypatch.setattr(firestore_utils, "db", DummyDB())
    with caplog.at_level(logging.ERROR):
        count, hours = firestore_utils.fetch_attendance_summary("code", "ClassA")
    assert count == 0 and hours == 0.0
    assert any("Failed to fetch attendance summary" in r.message for r in caplog.records)
