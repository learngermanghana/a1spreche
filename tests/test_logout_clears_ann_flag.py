from unittest.mock import MagicMock
import types

from src.logout import do_logout


def test_ann_flag_reset_after_logout():
    mock_st = types.SimpleNamespace(
        session_state={"_ann_hash": "abc"},
        query_params={},
        success=MagicMock(),
    )
    do_logout(st_module=mock_st, destroy_token=MagicMock(), logger=types.SimpleNamespace(exception=MagicMock()))
    assert "_ann_hash" not in mock_st.session_state
    assert mock_st.session_state.get("need_rerun") is True
