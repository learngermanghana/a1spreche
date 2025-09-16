import ast
import types
from pathlib import Path
from datetime import UTC
import logging
import pandas as pd

from src.contracts import is_contract_expired
from src.services.contracts import contract_active


def _load_login_func():
    src_path = Path(__file__).resolve().parents[1] / "src/ui/auth.py"
    mod_ast = ast.parse(src_path.read_text())
    func_node = next(
        n for n in mod_ast.body if isinstance(n, ast.FunctionDef) and n.name == "render_login_form"
    )
    temp_module = ast.Module(body=[func_node], type_ignores=[])
    code = compile(temp_module, filename="auth.py", mode="exec")

    mod = types.ModuleType("login_test_module")
    mod.pd = pd
    mod.UTC = UTC
    mod.is_contract_expired = is_contract_expired
    mod.contract_active = contract_active
    mod.logging = logging
    mod.renew_session_if_needed = lambda: None

    errors: list[str] = []

    class DummyStreamlit:
        def error(self, msg):
            errors.append(msg)

    mod.st = DummyStreamlit()

    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=40)).strftime("%Y-%m-%d")
    end = (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    df = pd.DataFrame(
        [
            {
                "StudentCode": "abc",
                "Email": "abc@example.com",
                "Name": "Alice",
                "ContractStart": start,
                "ContractEnd": end,
                "Balance": 5,
            }
        ]
    )
    mod.load_student_data = lambda: df

    exec(code, mod.__dict__)
    return mod.render_login_form, errors


def test_login_rejected_when_balance_overdue():
    render_login_form, errors = _load_login_func()
    ok = render_login_form("abc", "pw")
    assert ok is False
    assert errors and "Outstanding balance past due" in errors[0]
