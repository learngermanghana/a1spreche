import types
from src import keychain


def test_get_token_returns_saved(monkeypatch):
    def fake_run(args, input, check, stdout, stderr):
        return types.SimpleNamespace(stdout=b"saved-token")
    monkeypatch.setattr(keychain, "_SWIFT_BIN", "swift")
    monkeypatch.setattr(keychain.subprocess, "run", fake_run)
    token = keychain.get_token(keychain.KeychainKey.accessToken)
    assert token == "saved-token"


def test_get_token_handles_absence(monkeypatch):
    monkeypatch.setattr(keychain, "_SWIFT_BIN", None)
    assert keychain.get_token(keychain.KeychainKey.accessToken) is None
