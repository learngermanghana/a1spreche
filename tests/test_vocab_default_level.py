import ast
import types
from pathlib import Path
import pandas as pd

def _load_module(df):
    src = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    mod_ast = ast.parse(src.read_text())
    func_nodes = [n for n in mod_ast.body if isinstance(n, ast.FunctionDef) and n.name == "load_vocab_lists"]
    temp_module = ast.Module(body=func_nodes, type_ignores=[])
    code = compile(temp_module, filename="a1sprechen.py", mode="exec")

    # Dummy streamlit with error/warning capture and cache_data decorator
    class DummyStreamlit:
        def __init__(self):
            self.errors = []
            self.warnings = []
        def error(self, msg):
            self.errors.append(msg)
        def warning(self, msg):
            self.warnings.append(msg)
    def cache_data(func=None, **kwargs):
        if func is None:
            def wrapper(f):
                return f
            return wrapper
        return func
    st = DummyStreamlit()
    st.cache_data = cache_data

    mod = types.ModuleType("temp_vocab_module")
    mod.pd = pd
    mod.st = st
    mod.SHEET_ID = "dummy"
    mod.SHEET_GID = 0

    # Patch read_csv to return our DataFrame
    mod.pd.read_csv = lambda url: df

    exec(code, mod.__dict__)
    return mod, st


def test_missing_level_defaults_to_a1():
    df = pd.DataFrame({"German": ["Hallo"], "English": ["Hello"]})
    mod, st = _load_module(df)
    vocab, audio = mod.load_vocab_lists()

    assert st.warnings, "Expected a warning when Level column is missing"
    assert not st.errors, "Should not report errors when Level is missing"
    assert vocab == {"A1": [("Hallo", "Hello")]}
    assert audio[("A1", "Hallo")] == {"normal": "", "slow": ""}
