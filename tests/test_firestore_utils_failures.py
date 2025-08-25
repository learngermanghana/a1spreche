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
        firestore_utils.save_draft_to_db("code", "draft_X", "text")
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
        firestore_utils.save_chat_draft_to_db("code", "conv", "hi")
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
        firestore_utils.save_chat_draft_to_db("code", "conv", "")
    assert any(record.levelno == logging.WARNING for record in caplog.records)
