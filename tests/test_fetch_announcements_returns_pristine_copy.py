import ast
import types
from pathlib import Path

import pandas as pd


def _load_fetch_module():
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    tree = ast.parse(src_path.read_text())
    mod = types.ModuleType("_fetch_mod")

    class FakeStreamlit:
        def __init__(self):
            self.session_state = {}
            self.secrets = {}

        def cache_data(self, *args, **kwargs):
            def decorator(func):
                return func
            if args and callable(args[0]) and not kwargs:
                return args[0]
            return decorator

    mod.st = FakeStreamlit()
    mod.pd = pd

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in (
            "_fetch_announcements_csv_cached",
            "fetch_announcements_csv",
        ):
            code = compile(ast.Module(body=[node], type_ignores=[]), filename=str(src_path), mode="exec")
            exec(code, mod.__dict__)
    return mod


def test_fetch_announcements_returns_pristine_copy():
    mod = _load_fetch_module()
    original = pd.DataFrame({"Announcement": ["Hello"]})
    mod._fetch_announcements_csv_cached = lambda: original.copy()

    first = mod.fetch_announcements_csv()
    first.loc[0, "Announcement"] = "Changed"
    first["Extra"] = 1

    second = mod.fetch_announcements_csv()
    pd.testing.assert_frame_equal(second, original)
