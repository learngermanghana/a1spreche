from unittest.mock import MagicMock
import types

from src import ui_widgets
from src.logout import do_logout


def test_logout_rerenders_components():
    mock_st = types.SimpleNamespace(
        session_state={},
        success=MagicMock(),
        markdown=MagicMock(),
        link_button=MagicMock(),
    )
    mock_components = types.SimpleNamespace(html=MagicMock())
    ui_widgets.st = mock_st
    ui_widgets.components = mock_components
    ui_widgets.render_announcements = MagicMock()

    ui_widgets.render_announcements_once([{"title": "t", "body": "b"}], True)
    assert mock_st.session_state.get("_ann_hash")
    ui_widgets.render_announcements.assert_called_once()

    mock_st.markdown.reset_mock()
    ui_widgets.render_google_brand_button_once("https://auth.example")
    assert mock_st.session_state.get("_google_cta_rendered") is True
    mock_st.markdown.assert_called_once()

    mock_st.markdown.reset_mock()
    ui_widgets.render_google_button_once("https://auth.example", key="primary")
    assert mock_st.session_state.get("__google_btn_rendered::primary") is True
    mock_st.markdown.assert_called_once()

    mock_components.html.reset_mock()
    ui_widgets.render_google_signin_once("https://auth.example")
    assert mock_st.session_state.get("_google_btn_rendered") is True
    mock_components.html.assert_called_once()

    ui_widgets.render_announcements.reset_mock()
    mock_components.html.reset_mock()
    mock_st.markdown.reset_mock()
    do_logout({}, st_module=mock_st, destroy_token=MagicMock(), clear_session_fn=MagicMock(), logger=types.SimpleNamespace(exception=MagicMock()))
    assert "_ann_hash" not in mock_st.session_state
    assert "_google_cta_rendered" not in mock_st.session_state
    assert "__google_btn_rendered::primary" not in mock_st.session_state
    assert "_google_btn_rendered" not in mock_st.session_state

    ui_widgets.render_announcements_once([{"title": "t", "body": "b"}], True)
    ui_widgets.render_announcements.assert_called_once()

    mock_st.markdown.reset_mock()
    ui_widgets.render_google_brand_button_once("https://auth.example")
    mock_st.markdown.assert_called_once()

    mock_st.markdown.reset_mock()
    ui_widgets.render_google_button_once("https://auth.example", key="primary")
    mock_st.markdown.assert_called_once()

    mock_components.html.reset_mock()
    ui_widgets.render_google_signin_once("https://auth.example")
    mock_components.html.assert_called_once()
    
    assert mock_st.session_state.get("need_rerun") is True


def test_logout_saves_cookie_changes():
    mock_st = types.SimpleNamespace(session_state={}, success=MagicMock())
    cookie_manager = types.SimpleNamespace(save=MagicMock())
    clear_session = MagicMock()
    do_logout(
        cookie_manager,
        st_module=mock_st,
        destroy_token=MagicMock(),
        clear_session_fn=clear_session,
        logger=types.SimpleNamespace(exception=MagicMock()),
    )
    clear_session.assert_called_once_with(cookie_manager)
    cookie_manager.save.assert_called_once()
    assert mock_st.session_state.get("need_rerun") is True
