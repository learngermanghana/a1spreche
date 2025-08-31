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
        if isinstance(node, ast.FunctionDef) and node.name == "render_announcements_once":
            nodes.append(node)
    mod = types.ModuleType("ann_module")
    mod.__file__ = str(path)
    mod.st = types.SimpleNamespace(
        session_state={},
        warning=MagicMock(),
        error=MagicMock(),
    )
    mod.render_announcements = MagicMock(side_effect=Exception("boom"))
    mod.logging = types.SimpleNamespace(exception=MagicMock())
    code = compile(ast.Module(body=nodes, type_ignores=[]), "ann_module", "exec")
    exec(code, mod.__dict__)
    return mod


def test_render_announcements_once_handles_exception():
    mod = load_module()
    mod.render_announcements_once([{ "title": "t", "body": "b" }])
    mod.render_announcements.assert_called_once()
    mod.logging.exception.assert_called_once()
    mod.st.warning.assert_called_once()
    assert "_ann_rendered" not in mod.st.session_state
