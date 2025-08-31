import ast, types, pathlib
from unittest.mock import MagicMock
import pytest

def load_go_module():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    module_ast = ast.parse(source)
    qp_func = go_func = None
    for node in ast.walk(module_ast):
        if isinstance(node, ast.FunctionDef) and node.name == "render_sidebar_published":
            for inner in node.body:
                if isinstance(inner, ast.FunctionDef):
                    if inner.name == "_qp_set_safe":
                        qp_func = inner
                    elif inner.name == "_go":
                        go_func = inner
            break
    mod = types.ModuleType("go_module")
    mod.st = types.SimpleNamespace(session_state={}, rerun=MagicMock(), query_params={})
    code = compile(ast.Module(body=[qp_func, go_func], type_ignores=[]), "go_module", "exec")
    exec(code, mod.__dict__)
    return mod

def test_go_sets_rerun_flag():
    mod = load_go_module()
    mod._go("Dashboard")
    assert mod.st.session_state.get("needs_rerun") is True
    mod.st.rerun.assert_not_called()
