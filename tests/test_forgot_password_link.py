import ast
import pathlib


def load_returning_login_func():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "render_returning_login_area":
            return node
    raise AssertionError("render_returning_login_area not found")


def test_forgot_password_button_present():
    func = load_returning_login_func()
    found = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"form_submit_button", "button"}:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and "Forgot password" in str(arg.value):
                        found = True
                        break
    assert found, "Forgot password button missing"


def test_calls_forgot_password_panel():
    func = load_returning_login_func()
    found = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "render_forgot_password_panel":
                found = True
                break
    assert found, "render_forgot_password_panel not called in render_returning_login_area"
