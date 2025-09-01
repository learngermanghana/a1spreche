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
        if isinstance(node, ast.FunctionDef) and node.name == "_do_logout":
            nodes.append(node)
    mod = types.ModuleType("logout_module")
    mod.__file__ = str(path)
    mod.st = types.SimpleNamespace(
        session_state={"_ann_hash": "abc"},
        success=MagicMock(),
        rerun=MagicMock(),
    )
    mod.clear_session = MagicMock()
    mod.destroy_session_token = MagicMock()
    mod.cookie_manager = object()
    mod.logging = types.SimpleNamespace(exception=MagicMock())
    code = compile(ast.Module(body=nodes, type_ignores=[]), "logout_module", "exec")
    exec(code, mod.__dict__)
    return mod


def test_ann_flag_reset_after_logout():
    mod = load_module()
    assert mod.st.session_state.get("_ann_hash") == "abc"
    mod._do_logout()
    assert "_ann_hash" not in mod.st.session_state
