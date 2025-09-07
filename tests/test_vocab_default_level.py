import pandas as pd
import src.services.vocab as vocab


def test_missing_level_defaults_to_a1(monkeypatch):
    df = pd.DataFrame({"German": ["Hallo"], "English": ["Hello"]})

    class DummyStreamlit:
        def __init__(self):
            self.errors = []
            self.warnings = []

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
