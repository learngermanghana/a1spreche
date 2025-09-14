from types import SimpleNamespace

from src.logout import do_logout


def test_logout_clears_state_and_query_params():
    destroyed = []
    mock_st = SimpleNamespace(
        session_state={"session_token": "tok", "student_code": "abc", "logged_in": True},
        query_params={"t": "tok"},
        success=lambda *a, **k: None,
    )

    def fake_destroy(tok):
        destroyed.append(tok)

    do_logout(st_module=mock_st, destroy_token=fake_destroy)
    assert mock_st.session_state["session_token"] == ""
    assert mock_st.session_state["student_code"] == ""
    assert "t" not in mock_st.query_params
    assert destroyed == ["tok"]
