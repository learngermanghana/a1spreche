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
        "fetch_announcements_csv",
        "render_announcements_once",
    }
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            nodes.append(node)
    mod = types.ModuleType("logout_module")
    mod.__file__ = str(path)
    mod.st = types.SimpleNamespace(
        session_state={"logged_in": True},
        success=MagicMock(),
        rerun=MagicMock(),
    )
    mod.clear_session = MagicMock()
    mod.destroy_session_token = MagicMock()
    mod.cookie_manager = object()
    mod.logging = types.SimpleNamespace(exception=MagicMock())
    mod.render_announcements = MagicMock()
    data1 = types.SimpleNamespace(copy=MagicMock(return_value="df1"))
    data2 = types.SimpleNamespace(copy=MagicMock(return_value="df2"))
    mod._fetch_announcements_csv_cached = MagicMock(side_effect=[data1, data2])
    code = compile(ast.Module(body=nodes, type_ignores=[]), "logout_module", "exec")
    exec(code, mod.__dict__)
    return mod


def test_announcements_render_after_double_logout():
    mod = load_module()

    # Initial login and fetch
    assert mod.fetch_announcements_csv() == "df1"
    assert mod._fetch_announcements_csv_cached.call_count == 1
    mod.render_announcements_once([{"title": "t", "body": "b"}])
    mod.render_announcements.assert_called_once()

    # Logout twice
    mod._do_logout()
    mod._do_logout()

    # Simulate logging in again
    mod.st.session_state["logged_in"] = True
    mod.render_announcements.reset_mock()

    # Fresh fetch and render
    assert mod.fetch_announcements_csv() == "df2"
    assert mod._fetch_announcements_csv_cached.call_count == 2
    mod.render_announcements_once([{"title": "t2", "body": "b2"}])
    mod.render_announcements.assert_called_once()
