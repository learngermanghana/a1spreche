import ast
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

class DummyCtx:
    def __enter__(self):
        return None
    def __exit__(self, exc_type, exc, tb):
        return False


def load_login_page():
    src = Path('a1sprechen.py').read_text()
    module = ast.parse(src, filename='a1sprechen.py')
    login_node = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'login_page'
    )
    code = compile(ast.Module(body=[login_node], type_ignores=[]), filename='login_page', mode='exec')
    ns = {}
    exec(code, ns)
    return ns['login_page'], ns


def make_streamlit_stub():
    st = types.SimpleNamespace(session_state={}, markdown=MagicMock(), info=MagicMock())
    def tabs(labels):
        return (DummyCtx(), DummyCtx())
    st.tabs = tabs
    def columns(n):
        return [DummyCtx() for _ in range(n)]
    st.columns = columns
    return st


def run_login_page():
    login_page, ns = load_login_page()
    st = make_streamlit_stub()
    ns.update({
        'st': st,
        'render_google_oauth': MagicMock(return_value='auth'),
        'render_falowen_login': MagicMock(),
        'render_returning_login_area': MagicMock(return_value=False),
        'render_signup_request_banner': MagicMock(),
        'render_signup_form': MagicMock(),
        'render_google_brand_button_once': MagicMock(),
    })
    fetch_mock = MagicMock(return_value=[{'title': 't'}])
    render_mock = MagicMock()
    ns['fetch_blog_feed'] = fetch_mock
    ns['render_announcements'] = render_mock
    login_page.__globals__.update(ns)
    return login_page, fetch_mock, render_mock


def test_announcements_render_for_logged_out_and_after_signup():
    login_page, fetch_mock, render_mock = run_login_page()
    login_page()
    fetch_mock.assert_called_once()
    render_mock.assert_called_once_with([{'title': 't'}])

    fetch_mock.reset_mock()
    render_mock.reset_mock()
    login_page()
    fetch_mock.assert_called_once()
    render_mock.assert_called_once_with([{'title': 't'}])
