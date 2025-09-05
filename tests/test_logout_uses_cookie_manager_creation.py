from unittest.mock import MagicMock
import types

from src.logout import do_logout


def test_logout_creates_cookie_manager_and_clears_without_save():
    cm = types.SimpleNamespace(save=MagicMock())
    create_cm = MagicMock(return_value=cm)
    clear_session = MagicMock()
    mock_st = types.SimpleNamespace(session_state={}, success=MagicMock())

    do_logout(
        None,
        st_module=mock_st,
        destroy_token=MagicMock(),
        clear_session_fn=clear_session,
        create_cookie_manager_fn=create_cm,
        logger=types.SimpleNamespace(exception=MagicMock()),
    )

    create_cm.assert_called_once_with()
    clear_session.assert_called_once_with(cm)
    cm.save.assert_not_called()
