import ast
import pathlib
import types
from unittest.mock import MagicMock


def load_module():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    module_ast = ast.parse(source)
    nodes = []
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name in {"_do_logout", "render_google_signin_once"}:
            nodes.append(node)
    mod = types.ModuleType("logout_module")
    mod.__file__ = str(path)
    mod.st = types.SimpleNamespace(
        session_state={},
        success=MagicMock(),
        rerun=MagicMock(),
        link_button=MagicMock(),
    )
    mod.components = types.SimpleNamespace(html=MagicMock())
    mod.clear_session = MagicMock()
    mod.destroy_session_token = MagicMock()
    mod.cookie_manager = object()
    mod.logging = types.SimpleNamespace(exception=MagicMock())
    code = compile(ast.Module(body=nodes, type_ignores=[]), "logout_module", "exec")
    exec(code, mod.__dict__)
    return mod


def test_google_button_reappears_after_logout():
    mod = load_module()

    # Initial render simulates login page showing the button
    mod.render_google_signin_once("https://auth.example")
    assert mod.st.session_state.get("_google_btn_rendered") is True
    mod.components.html.assert_called_once()

    # After logout the flag should be cleared
    mod.components.html.reset_mock()
    mod._do_logout()
    assert "_google_btn_rendered" not in mod.st.session_state

    # Rendering login again should call html once more
    mod.render_google_signin_once("https://auth.example")
    mod.components.html.assert_called_once()
