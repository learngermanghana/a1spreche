import pytest
import streamlit as st

from src.session_management import bootstrap_cookie_manager


class _ToggleReady:
    def __init__(self, fail_until: int = 2) -> None:
        self._count = 0
        self._fail_until = fail_until

    def ready(self) -> bool:
        self._count += 1
        return self._count > self._fail_until


def test_bootstrap_cookie_manager_waits_for_ready(monkeypatch):
    cm = _ToggleReady()
    monkeypatch.setattr("src.session_management.time.sleep", lambda s: None)

    def _fail_stop():
        raise AssertionError("st.stop should not be called")

    monkeypatch.setattr(st, "stop", _fail_stop)
    assert bootstrap_cookie_manager(cm, attempts=5, delay=0.01) is cm
    assert cm._count > 2


def test_bootstrap_cookie_manager_stops_if_never_ready(monkeypatch):
    class _NeverReady:
        def ready(self) -> bool:
            return False

    cm = _NeverReady()
    monkeypatch.setattr("src.session_management.time.sleep", lambda s: None)
    called = []

    def _stop():
        called.append(True)
        raise RuntimeError("stop")

    monkeypatch.setattr(st, "stop", _stop)
    with pytest.raises(RuntimeError):
        bootstrap_cookie_manager(cm, attempts=2, delay=0.01)
    assert called == [True]
