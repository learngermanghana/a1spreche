import src.stats as stats


def test_vocab_attempt_exists_without_db():
    stats.db = None
    assert stats.vocab_attempt_exists("student", "session") is False


def test_get_vocab_stats_without_db():
    stats.db = None
    result = stats.get_vocab_stats("student")
    assert result["history"] == []
    assert result["total_sessions"] == 0



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
