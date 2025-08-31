import ast
from pathlib import Path
from datetime import UTC
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.contracts import is_contract_expired


def _load_contract_active():
    """Load the `_contract_active` function from `a1sprechen.py` without executing
    the whole module."""

    src = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    mod_ast = ast.parse(src.read_text())
    func_node = next(
        n for n in mod_ast.body if isinstance(n, ast.FunctionDef) and n.name == "_contract_active"
    )
    temp_module = ast.Module(body=[func_node], type_ignores=[])
    code = compile(temp_module, filename="a1sprechen.py", mode="exec")
    ns: dict = {}
    exec(code, {"pd": pd, "UTC": UTC, "is_contract_expired": is_contract_expired}, ns)
    return ns["_contract_active"]


def test_contract_inactive_when_expired():
    _contract_active = _load_contract_active()
    df = pd.DataFrame([{"StudentCode": "abc", "ContractEnd": "2020-01-01"}])
    assert _contract_active("abc", df) is False


def test_contract_inactive_when_balance_over_30_days():
    _contract_active = _load_contract_active()
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=40)).strftime("%Y-%m-%d")
    end = (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=20)).strftime("%Y-%m-%d")
    df = pd.DataFrame(
        [
            {
                "StudentCode": "abc",
                "ContractStart": start,
                "ContractEnd": end,
                "Balance": 10,
            }
        ]
    )
    assert _contract_active("abc", df) is False


def test_balance_string_with_comma_blocks_login():
    _contract_active = _load_contract_active()
    start = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=35)).strftime("%Y-%m-%d")
    end = (pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    df = pd.DataFrame(
        [
            {
                "StudentCode": "abc",
                "ContractStart": start,
                "ContractEnd": end,
                "Balance": "1,000",
            }
        ]
    )
    assert _contract_active("abc", df) is False

