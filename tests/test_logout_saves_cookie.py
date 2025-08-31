import ast
import pathlib
import types
from unittest.mock import MagicMock


def load_module():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    module_ast = ast.parse(source)
    nodes = [n for n in module_ast.body if isinstance(n, ast.FunctionDef) and n.name == "_do_logout"]
    mod = types.ModuleType("logout_mod")
    mod.__file__ = str(path)
    mod.st = types.SimpleNamespace(
        session_state={},
        success=MagicMock(),
        rerun=MagicMock(),
    )
    cm = types.SimpleNamespace(save=MagicMock())
    mod.cookie_manager = cm
    mod.clear_session = MagicMock()
    mod.destroy_session_token = MagicMock()
    mod.logging = types.SimpleNamespace(exception=MagicMock())
    code = compile(ast.Module(body=nodes, type_ignores=[]), "logout_mod", "exec")
    exec(code, mod.__dict__)
    return mod, cm


def test_logout_saves_cookies():
    mod, cm = load_module()
    mod._do_logout()
    cm.save.assert_called_once()
