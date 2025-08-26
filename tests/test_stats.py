from datetime import UTC, datetime

import src.stats as stats


def test_vocab_attempt_exists_without_db():
    stats.db = None
    assert stats.vocab_attempt_exists("student", "session") is False


def test_get_vocab_stats_without_db():
    stats.db = None
    result = stats.get_vocab_stats("student")
    assert result["history"] == []
    assert result["total_sessions"] == 0

def test_vocab_attempt_exists_handles_get_failure(monkeypatch):
    class BoomDoc:
        def get(self):
            raise Exception("boom")

    class BoomCollection:
        def document(self, key):
            return BoomDoc()

    class BoomDB:
        def collection(self, name):
            return BoomCollection()

    warnings = []
    stats.db = BoomDB()
    monkeypatch.setattr(stats.st, "warning", lambda msg: warnings.append(msg))
    assert stats.vocab_attempt_exists("stud", "sess") is False
    assert warnings

class DummyDoc:
    def __init__(self, store, key):
        self.store = store
        self.key = key

    def get(self):
        data = self.store.get(self.key)
        class Result:
            def __init__(self, exists, data):
                self.exists = exists
                self._data = data or {}

            def to_dict(self):
                return self._data

        if data is None:
            return Result(False, {})
        return Result(True, data)

    def set(self, data, merge=False):
        if merge and self.key in self.store:
            self.store[self.key].update(data)
        else:
            self.store[self.key] = data


class DummyCollection:
    def __init__(self, storage):
        self.storage = storage

    def document(self, key):
        return DummyDoc(self.storage, key)


class DummyDB:
    def __init__(self):
        self.data = {}

    def collection(self, name):
        coll = self.data.setdefault(name, {})
        return DummyCollection(coll)


def test_save_vocab_attempt_truncates_history():
    stats.db = DummyDB()
    extra = 5
    total = stats.MAX_HISTORY + extra
    for i in range(total):
        stats.save_vocab_attempt(
            "stud", "A1", 10, 5, [], session_id=f"s{i}"
        )

    result = stats.get_vocab_stats("stud")
    assert len(result["history"]) == stats.MAX_HISTORY
    assert result["total_sessions"] == total
    assert result["history"][0]["session_id"] == f"s{extra}"
    assert result["history"][-1]["session_id"] == f"s{total - 1}"

def test_load_student_levels_uses_env_var(monkeypatch):
    captured = {}

    def fake_read_csv(url):
        captured["url"] = url
        return stats.pd.DataFrame({"student_code": [], "level": []})

    monkeypatch.setattr(stats.pd, "read_csv", fake_read_csv)
    monkeypatch.setattr(stats.st, "secrets", {})
    monkeypatch.setenv("ROSTER_SHEET_ID", "ENV123")
    stats.load_student_levels.clear()
    stats.load_student_levels()
    assert "ENV123" in captured["url"]


def test_load_student_levels_uses_secrets(monkeypatch):
    captured = {}

    def fake_read_csv(url):
        captured["url"] = url
        return stats.pd.DataFrame({"student_code": [], "level": []})

    monkeypatch.setattr(stats.pd, "read_csv", fake_read_csv)
    monkeypatch.delenv("ROSTER_SHEET_ID", raising=False)
    monkeypatch.setattr(stats.st, "secrets", {"ROSTER_SHEET_ID": "SECRET456"})
    stats.load_student_levels.clear()
    stats.load_student_levels()
    assert "SECRET456" in captured["url"]


def test_load_student_levels_handles_failure(monkeypatch):
    def fail_read_csv(url):
        raise OSError("fail")

    warnings = []
    monkeypatch.setattr(stats.pd, "read_csv", fail_read_csv)
    monkeypatch.setattr(stats.st, "warning", lambda msg: warnings.append(msg))
    stats.load_student_levels.clear()
    df = stats.load_student_levels()
    assert warnings  # warning was emitted
    assert list(df.columns) == ["student_code", "level"]
    assert df.empty


def test_save_vocab_attempt_sanitizes_negative_inputs(monkeypatch):
    stats.db = DummyDB()
    warnings = []
    monkeypatch.setattr(stats.st, "warning", lambda msg: warnings.append(msg))
    stats.save_vocab_attempt("stud", "A1", -5, -2, [])
    attempt = stats.get_vocab_stats("stud")["history"][-1]
    assert attempt["total"] == 0
    assert attempt["correct"] == 0
    assert any("Total" in w for w in warnings)
    assert any("Correct" in w for w in warnings)


def test_save_vocab_attempt_limits_correct_to_total(monkeypatch):
    stats.db = DummyDB()
    warnings = []
    monkeypatch.setattr(stats.st, "warning", lambda msg: warnings.append(msg))
    stats.save_vocab_attempt("stud", "A1", 3, 5, [])
    attempt = stats.get_vocab_stats("stud")["history"][-1]
    assert attempt["total"] == 3
    assert attempt["correct"] == 3
    assert any("exceeds total" in w for w in warnings)


def test_save_vocab_attempt_handles_set_failure(monkeypatch):
    class BoomDoc:
        def __init__(self):
            self.exists = False

        def get(self):
            class Result:
                exists = False

                def to_dict(self):
                    return {}

            return Result()

        def set(self, *args, **kwargs):
            raise Exception("boom")

    class BoomCollection:
        def document(self, key):
            return BoomDoc()

    class BoomDB:
        def collection(self, name):
            return BoomCollection()

    warnings = []
    stats.db = BoomDB()
    monkeypatch.setattr(stats.st, "warning", lambda msg: warnings.append(msg))
    stats.save_vocab_attempt("stud", "A1", 1, 1, [])
    assert warnings


def test_get_vocab_stats_handles_get_failure(monkeypatch):
    class BoomDoc:
        def get(self):
            raise Exception("boom")

    class BoomCollection:
        def document(self, key):
            return BoomDoc()

    class BoomDB:
        def collection(self, name):
            return BoomCollection()

    warnings = []
    stats.db = BoomDB()
    monkeypatch.setattr(stats.st, "warning", lambda msg: warnings.append(msg))
    result = stats.get_vocab_stats("stud")
    assert result["history"] == []
    assert result["total_sessions"] == 0
    assert warnings


def test_save_vocab_attempt_uses_utc_timestamp():
    stats.db = DummyDB()
    stats.save_vocab_attempt("stud", "A1", 1, 1, [])
    attempt = stats.get_vocab_stats("stud")["history"][-1]
    dt = datetime.fromisoformat(attempt["timestamp"])
    assert dt.tzinfo == UTC
