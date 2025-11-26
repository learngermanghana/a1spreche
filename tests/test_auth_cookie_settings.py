from types import SimpleNamespace

import src.auth as auth


def test_cookie_ttl_respects_env(monkeypatch):
    monkeypatch.setenv("SESSION_MAX_AGE_DAYS", "5")
    assert auth._cookie_ttl_seconds() == 5 * 24 * 60 * 60


def test_cookie_ttl_default(monkeypatch):
    monkeypatch.delenv("SESSION_MAX_AGE_DAYS", raising=False)
    assert auth._cookie_ttl_seconds() == 90 * 24 * 60 * 60


def test_persist_session_client_writes_cookies(monkeypatch):
    monkeypatch.delenv("SESSION_MAX_AGE_DAYS", raising=False)

    class FakeCM(dict):
        ready = True

        def set(self, key, value, **kwargs):
            self[key] = (value, kwargs)

        def save(self):
            self["saved"] = True

    cm = FakeCM()
    mock_st = SimpleNamespace(session_state={}, query_params={})

    class Logger:
        def __init__(self):
            self.warnings = []
            self.exceptions = []
            self.debugs = []

        def warning(self, msg, *args, **kwargs):
            self.warnings.append(msg % args if args else msg)

        def exception(self, msg, *args, **kwargs):
            self.exceptions.append(msg % args if args else msg)

        def debug(self, msg, *args, **kwargs):
            self.debugs.append(msg % args if args else msg)

    logger = Logger()
    auth.persist_session_client(
        "tok123",
        "code456",
        cookie_manager=cm,
        st_module=mock_st,
        logger=logger,
    )

    assert mock_st.session_state["session_token"] == "tok123"
    assert mock_st.session_state["student_code"] == "code456"
    assert mock_st.query_params["t"] == "tok123"
    assert "falowen_session_token" in cm
    assert "falowen_student_code" in cm
    assert "falowen_session_expiry" in cm
    assert cm.get("saved") is True
    assert not logger.exceptions


def test_persist_session_prefers_cookie_device_id(monkeypatch):
    monkeypatch.delenv("SESSION_MAX_AGE_DAYS", raising=False)

    class FakeCM(dict):
        ready = True

        def __init__(self):
            super().__init__()
            self[auth._COOKIE_DEVICE_KEY] = "cookie-device"

        def set(self, key, value, **kwargs):
            self[key] = (value, kwargs)

        def save(self):
            self["saved"] = True

    cm = FakeCM()
    mock_st = SimpleNamespace(session_state={"device_id": "stale"}, query_params={})

    class Logger:
        def __init__(self):
            self.warnings = []
            self.exceptions = []
            self.debugs = []

        def warning(self, msg, *args, **kwargs):
            self.warnings.append(msg % args if args else msg)

        def exception(self, msg, *args, **kwargs):
            self.exceptions.append(msg % args if args else msg)

        def debug(self, msg, *args, **kwargs):
            self.debugs.append(msg % args if args else msg)

    logger = Logger()

    auth.persist_session_client(
        "tok123",
        "code456",
        cookie_manager=cm,
        st_module=mock_st,
        logger=logger,
    )

    stored_device = cm.get(auth._COOKIE_DEVICE_KEY)
    if isinstance(stored_device, tuple):
        stored_device = stored_device[0]

    assert mock_st.session_state["device_id"] == "cookie-device"
    assert stored_device == "cookie-device"
    assert any("device_id" in msg for msg in logger.debugs)
    assert not logger.exceptions


def test_persist_session_without_cookie_manager(monkeypatch):
    mock_st = SimpleNamespace(session_state={}, query_params={})

    class Logger:
        def __init__(self):
            self.warnings = []
            self.exceptions = []

        def warning(self, msg, *args, **kwargs):
            self.warnings.append(msg % args if args else msg)

        def exception(self, msg, *args, **kwargs):
            self.exceptions.append(msg % args if args else msg)

    logger = Logger()
    monkeypatch.setattr(auth, "get_cookie_manager", lambda: None)

    auth.persist_session_client(
        "tok123",
        "code456",
        cookie_manager=None,
        st_module=mock_st,
        logger=logger,
    )

    assert mock_st.session_state["session_token"] == "tok123"
    assert mock_st.session_state["student_code"] == "code456"
    assert mock_st.query_params["t"] == "tok123"
    assert logger.warnings
    assert not logger.exceptions


def test_persist_session_respects_not_ready_cookie_manager(monkeypatch):
    mock_st = SimpleNamespace(session_state={}, query_params={})

    class NotReadyCM(dict):
        def ready(self):
            return False

    class Logger:
        def __init__(self):
            self.warnings = []
            self.debugs = []
            self.exceptions = []

        def warning(self, msg, *args, **kwargs):
            self.warnings.append(msg % args if args else msg)

        def exception(self, msg, *args, **kwargs):
            self.exceptions.append(msg % args if args else msg)

        def debug(self, msg, *args, **kwargs):
            self.debugs.append(msg % args if args else msg)

    logger = Logger()

    auth.persist_session_client(
        "tok123",
        "code456",
        cookie_manager=NotReadyCM(),
        st_module=mock_st,
        logger=logger,
    )

    assert mock_st.session_state["session_token"] == "tok123"
    assert mock_st.session_state["student_code"] == "code456"
    assert mock_st.query_params["t"] == "tok123"
    assert logger.warnings
    assert not logger.exceptions

