import sys
import types
import logging

import pandas as pd

from src.auth import SimpleCookieManager, set_session_token_cookie, set_student_code_cookie


def test_login_succeeds_when_cookie_save_fails(monkeypatch, caplog):
    errors: list[str] = []

    class FailingCookieManager(SimpleCookieManager):
        def save(self) -> None:  # pragma: no cover
            raise RuntimeError("boom")

    cm = FailingCookieManager()

    # Stub streamlit module
    st_module = types.ModuleType("streamlit")
    st_module.session_state = {"cookie_manager": cm, "__ua_hash": ""}

    def _err(msg: str) -> None:
        errors.append(msg)

    st_module.error = _err
    st_module.success = lambda *a, **k: None
    st_module.info = lambda *a, **k: None
    st_module.cache_data = lambda *a, **k: (lambda f: f)
    st_module.secrets = {}
    comps_v1 = types.ModuleType("streamlit.components.v1")
    comps_v1.html = lambda *a, **k: None
    components = types.ModuleType("streamlit.components")
    components.v1 = comps_v1
    st_module.components = components
    monkeypatch.setitem(sys.modules, "streamlit", st_module)
    monkeypatch.setitem(sys.modules, "streamlit.components", components)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", comps_v1)

    # Stub external dependencies
    email_utils = types.ModuleType("falowen.email_utils")
    email_utils.send_reset_email = lambda *a, **k: True
    email_utils.build_gas_reset_link = lambda token: f"https://example.com/{token}"
    monkeypatch.setitem(sys.modules, "falowen.email_utils", email_utils)

    class _Doc:
        exists = True

        def to_dict(self):
            return {"password": "pw"}

        def update(self, data):
            pass

    class _DocRef:
        def get(self):
            return _Doc()

        def update(self, data):
            pass

    class _DB:
        def collection(self, name):
            return types.SimpleNamespace(document=lambda code: _DocRef())

    sessions = types.ModuleType("falowen.sessions")
    sessions.create_session_token = lambda *a, **k: "tok"
    sessions.destroy_session_token = lambda *a, **k: None
    sessions.db = _DB()
    monkeypatch.setitem(sys.modules, "falowen.sessions", sessions)

    # Stub config.get_cookie_manager
    config = types.ModuleType("src.config")
    config.get_cookie_manager = lambda: cm
    monkeypatch.setitem(sys.modules, "src.config", config)

    import importlib

    auth_module = importlib.import_module("src.ui.auth")

    # Patch helpers in module
    monkeypatch.setattr(auth_module, "load_student_data", lambda: pd.DataFrame([
        {
            "StudentCode": "abc",
            "Email": "abc@example.com",
            "Name": "Alice",
            "ContractStart": "2020-01-01",
            "ContractEnd": "2030-01-01",
            "Balance": 0,
        }
    ]))
    monkeypatch.setattr(auth_module, "is_contract_expired", lambda row: False)
    monkeypatch.setattr(auth_module, "contract_active", lambda code, df: True)
    monkeypatch.setattr(auth_module, "determine_level", lambda code, row: 1)
    monkeypatch.setattr(auth_module, "persist_session_client", lambda *a, **k: None)
    monkeypatch.setattr(auth_module, "clear_session", lambda *a, **k: None)
    monkeypatch.setattr(auth_module, "toast_ok", lambda *a, **k: None)
    monkeypatch.setattr(auth_module, "set_session_token_cookie", set_session_token_cookie)
    monkeypatch.setattr(auth_module, "set_student_code_cookie", set_student_code_cookie)
    monkeypatch.setattr(auth_module, "get_cookie_manager", lambda: cm)

    with caplog.at_level(logging.DEBUG):
        ok = auth_module.render_login_form("abc", "pw")

    assert ok is True
    assert not errors
    assert any(r.levelno == logging.DEBUG and "Cookie save failed" in r.message for r in caplog.records)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)
