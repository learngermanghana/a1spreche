import src.stats as stats


def test_vocab_attempt_exists_without_db():
    stats.db = None
    assert stats.vocab_attempt_exists("student", "session") is False


def test_get_vocab_stats_without_db():
    stats.db = None
    result = stats.get_vocab_stats("student")
    assert result["history"] == []
    assert result["total_sessions"] == 0
