from unittest.mock import MagicMock
import types

from src.logout import do_logout


def test_ann_flag_reset_after_logout():
    mock_st = types.SimpleNamespace(
        session_state={"_ann_hash": "abc"},
        success=MagicMock(),
        rerun=MagicMock(),
    )
    do_logout({}, st_module=mock_st, destroy_token=MagicMock(), clear_session_fn=MagicMock(), logger=types.SimpleNamespace(exception=MagicMock()))
    assert "_ann_hash" not in mock_st.session_state
