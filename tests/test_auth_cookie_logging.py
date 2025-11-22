from types import SimpleNamespace
import time

import src.session_management as sm


def test_bootstrap_session_from_qp_seeds_state(monkeypatch):
    def fake_validate(tok, ua_hash=""):
        assert tok == "tok123"
        return {"student_code": "abc", "name": "Alice"}

    mock_st = SimpleNamespace(session_state={}, query_params={"t": "tok123"})
    monkeypatch.setattr(sm, "st", mock_st)
    monkeypatch.setattr(sm, "validate_session_token", fake_validate)

    sm.bootstrap_session_from_qp()
    assert mock_st.session_state["student_code"] == "abc"
    assert mock_st.session_state["session_token"] == "tok123"
    assert mock_st.query_params["t"] == "tok123"


def test_bootstrap_session_from_qp_no_token(monkeypatch):
    mock_st = SimpleNamespace(session_state={}, query_params={})
    monkeypatch.setattr(sm, "st", mock_st)

    sm.bootstrap_session_from_qp()
    assert mock_st.session_state == {}


def test_bootstrap_session_from_cookies(monkeypatch):
    def fake_validate(tok, ua_hash=""):
        assert tok == "tok-cookie"
        return {"student_code": "cookie-123", "name": "Cookie User"}

    def fake_cookie_manager():
        return {
            "falowen_session_token": "tok-cookie",
            "falowen_student_code": "cookie-123",
            "falowen_session_expiry": str(int(time.time()) + 60),
        }

    mock_st = SimpleNamespace(session_state={}, query_params={})
    monkeypatch.setattr(sm, "st", mock_st)
    monkeypatch.setattr(sm, "validate_session_token", fake_validate)
    monkeypatch.setattr(sm, "get_cookie_manager", fake_cookie_manager)

    sm.bootstrap_session_from_qp()

    assert mock_st.session_state["student_code"] == "cookie-123"
    assert mock_st.session_state["session_token"] == "tok-cookie"
    assert mock_st.session_state["cookie_synced"] is True
    assert mock_st.query_params["t"] == "tok-cookie"


def test_bootstrap_session_from_cookies_expired(monkeypatch):
    def fake_cookie_manager():
        return {
            "falowen_session_token": "tok-cookie",
            "falowen_student_code": "cookie-123",
            "falowen_session_expiry": str(int(time.time()) - 1),
        }

    mock_st = SimpleNamespace(session_state={}, query_params={})
    monkeypatch.setattr(sm, "st", mock_st)
    monkeypatch.setattr(sm, "get_cookie_manager", fake_cookie_manager)

    sm.bootstrap_session_from_qp()

    assert mock_st.session_state == {}
