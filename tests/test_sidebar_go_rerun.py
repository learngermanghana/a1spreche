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

@pytest.mark.parametrize(
    "tab",
    [
        "Dashboard",
        "My Course",
        "My Results and Resources",
        "Exams Mode & Custom Chat",
        "Vocab Trainer",
        "Schreiben Trainer",
    ],
)
def test_go_updates_state_and_triggers_rerun(tab: str):
    mod = load_go_module()
    mod._go(tab)
    assert mod.st.session_state["nav_sel"] == tab
    assert mod.st.session_state["main_tab_select"] == tab
    assert mod.st.session_state["needs_rerun"] is True
    if mod.st.session_state.pop("needs_rerun", False):
        mod.st.rerun()
    mod.st.rerun.assert_called_once()
