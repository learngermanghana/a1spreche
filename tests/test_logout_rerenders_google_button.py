import ast
import pathlib
import types
from unittest.mock import MagicMock


def load_module():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    module_ast = ast.parse(source)
    nodes = []
    wanted = {
        "_do_logout",
        "render_google_signin_once",
        "render_google_brand_button_once",
        "render_google_button_once",
        "render_announcements_once",
    }
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            nodes.append(node)
    mod = types.ModuleType("logout_module")
    mod.__file__ = str(path)
    mod.st = types.SimpleNamespace(
        session_state={},
        success=MagicMock(),
        rerun=MagicMock(),
        link_button=MagicMock(),
        markdown=MagicMock(),
    )
    mod.components = types.SimpleNamespace(html=MagicMock())
    mod.clear_session = MagicMock()
    mod.destroy_session_token = MagicMock()
    mod.cookie_manager = object()
    mod.logging = types.SimpleNamespace(exception=MagicMock())
    mod.render_announcements = MagicMock()
    mod.hashlib = __import__("hashlib")
    mod.json = __import__("json")
    code = compile(ast.Module(body=nodes, type_ignores=[]), "logout_module", "exec")
    exec(code, mod.__dict__)
    return mod


def test_logout_rerenders_components():
    mod = load_module()

    # Initial renders
    mod.render_announcements_once([{"title": "t", "body": "b"}], True)
    assert mod.st.session_state.get("_ann_hash")
    mod.render_announcements.assert_called_once()

    mod.st.markdown.reset_mock()
    mod.render_google_brand_button_once("https://auth.example")
    assert mod.st.session_state.get("_google_cta_rendered") is True
    mod.st.markdown.assert_called_once()

    mod.st.markdown.reset_mock()
    mod.render_google_button_once("https://auth.example", key="primary")
    assert mod.st.session_state.get("__google_btn_rendered::primary") is True
    mod.st.markdown.assert_called_once()

    mod.components.html.reset_mock()
    mod.render_google_signin_once("https://auth.example")
    assert mod.st.session_state.get("_google_btn_rendered") is True
    mod.components.html.assert_called_once()

    # After logout the flags should be cleared
    mod.render_announcements.reset_mock()
    mod.components.html.reset_mock()
    mod.st.markdown.reset_mock()
    mod._do_logout()
    assert "_ann_hash" not in mod.st.session_state
    assert "_google_cta_rendered" not in mod.st.session_state
    assert "__google_btn_rendered::primary" not in mod.st.session_state
    assert "_google_btn_rendered" not in mod.st.session_state

    # Re-render components after logout
    mod.render_announcements_once([{"title": "t", "body": "b"}], True)
    mod.render_announcements.assert_called_once()

    mod.st.markdown.reset_mock()
    mod.render_google_brand_button_once("https://auth.example")
    mod.st.markdown.assert_called_once()

    mod.st.markdown.reset_mock()
    mod.render_google_button_once("https://auth.example", key="primary")
    mod.st.markdown.assert_called_once()

    mod.components.html.reset_mock()
    mod.render_google_signin_once("https://auth.example")
    mod.components.html.assert_called_once()
