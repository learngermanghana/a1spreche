import pandas as pd
import src.services.vocab as vocab


class DummyStreamlit:
    def __init__(self, secrets=None):
        self.errors = []
        self.warnings = []
        self.secrets = secrets or {}

    def error(self, msg):
        self.errors.append(msg)

    def warning(self, msg):
        self.warnings.append(msg)

    def cache_data(self, func=None, **kwargs):
        if func is None:
            def wrapper(f):
                return f
            return wrapper
        return func


def test_missing_level_defaults_to_a1(monkeypatch):
    df = pd.DataFrame({"German": ["Hallo"], "English": ["Hello"]})

    st = DummyStreamlit()
    monkeypatch.setattr(vocab, "st", st)
    monkeypatch.setattr(vocab, "pd", pd)
    monkeypatch.setattr(vocab.pd, "read_csv", lambda url: df)
    vocab.load_vocab_lists.clear()

    vocab_lists, audio = vocab.load_vocab_lists()

    assert st.warnings, "Expected a warning when Level column is missing"
    assert not st.errors, "Should not report errors when Level is missing"
    assert vocab_lists == {"A1": [("Hallo", "Hello")]}
    assert audio[("A1", "Hallo")] == {"normal": "", "slow": ""}


def test_vocab_sheet_config_defaults(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setattr(vocab, "st", st)
    monkeypatch.delenv("VOCAB_SHEET_ID", raising=False)
    monkeypatch.delenv("VOCAB_SHEET_GID", raising=False)

    sheet_id, sheet_gid = vocab.get_vocab_sheet_config()

    assert sheet_id == vocab.DEFAULT_SHEET_ID
    assert sheet_gid == vocab.DEFAULT_SHEET_GID


def test_vocab_sheet_config_from_secrets(monkeypatch):
    st = DummyStreamlit({"vocab_sheet_id": "secret-id", "vocab_sheet_gid": 7})
    monkeypatch.setattr(vocab, "st", st)
    monkeypatch.delenv("VOCAB_SHEET_ID", raising=False)
    monkeypatch.delenv("VOCAB_SHEET_GID", raising=False)

    sheet_id, sheet_gid = vocab.get_vocab_sheet_config()

    assert sheet_id == "secret-id"
    assert sheet_gid == 7


def test_vocab_sheet_config_from_env(monkeypatch):
    st = DummyStreamlit()
    monkeypatch.setattr(vocab, "st", st)
    monkeypatch.setenv("VOCAB_SHEET_ID", "env-sheet")
    monkeypatch.setenv("VOCAB_SHEET_GID", "42")
    monkeypatch.setattr(vocab, "SHEET_ID", vocab.SHEET_ID, raising=False)
    monkeypatch.setattr(vocab, "SHEET_GID", vocab.SHEET_GID, raising=False)

    df = pd.DataFrame({"Level": ["A1"], "German": ["Hallo"], "English": ["Hello"]})
    captured = {}

    def fake_read_csv(url):
        captured["url"] = url
        return df

    monkeypatch.setattr(vocab, "pd", pd)
    monkeypatch.setattr(vocab.pd, "read_csv", fake_read_csv)
    vocab.load_vocab_lists.clear()

    vocab.load_vocab_lists()

    assert captured["url"].startswith(
        "https://docs.google.com/spreadsheets/d/env-sheet/export?format=csv&gid="
    )
    assert captured["url"].endswith("gid=42")
    assert vocab.SHEET_ID == "env-sheet"
    assert vocab.SHEET_GID == 42
