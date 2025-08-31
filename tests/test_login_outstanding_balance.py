import ast
import types
from pathlib import Path
from datetime import UTC
import pandas as pd
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.contracts import is_contract_expired


def _load_login_funcs():
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    mod_ast = ast.parse(src_path.read_text())
    nodes = [
        n
        for n in mod_ast.body
        if isinstance(n, ast.FunctionDef) and n.name in {"render_login_form", "_contract_active"}
    ]
    temp_module = ast.Module(body=nodes, type_ignores=[])
    code = compile(temp_module, filename="a1sprechen.py", mode="exec")

    mod = types.ModuleType("login_test_module")
    mod.pd = pd
    mod.UTC = UTC
    mod.is_contract_expired = is_contract_expired

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
    return mod, errors


def test_login_rejected_when_balance_overdue():
    mod, errors = _load_login_funcs()
    ok = mod.render_login_form("abc", "pw")
    assert ok is False
    assert errors and "Outstanding balance past due" in errors[0]
