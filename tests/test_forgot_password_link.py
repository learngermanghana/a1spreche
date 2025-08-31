import ast
import pathlib


def load_returning_login_func():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "render_returning_login_form":
            return node
    raise AssertionError("render_returning_login_form not found")


def test_forgot_password_button_present():
    func = load_returning_login_func()
    found = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "form_submit_button":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and "Forgot password" in str(arg.value):
                        found = True
                        break
    assert found, "Forgot password button missing"


def test_send_reset_email_used():
    func = load_returning_login_func()
    found = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "send_reset_email":
                found = True
                break
    assert found, "send_reset_email not called in render_returning_login_form"
