import importlib
import logging


def test_warning_emitted_when_fallback_cookie_password_used(monkeypatch, caplog):
    # Ensure environment and secrets do not provide a password
    monkeypatch.delenv("COOKIE_PASSWORD", raising=False)
    monkeypatch.delenv("FALOWEN_COOKIE_FALLBACK", raising=False)

    # Reload module to reset cached state
    config = importlib.reload(importlib.import_module("src.config"))
    monkeypatch.setattr(config.st, "secrets", {})

    with caplog.at_level(logging.WARNING):
        config.get_cookie_manager()

    assert any(
        "Using built-in fallback cookie password" in record.message
        for record in caplog.records
    )
