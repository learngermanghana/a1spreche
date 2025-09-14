from types import SimpleNamespace

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
