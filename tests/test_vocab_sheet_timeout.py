import ast
import types
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import requests
import io


def _get_vocab_loader():
    source = Path('a1sprechen.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    func_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_load_full_vocab_sheet_cached')
    func_src = ast.get_source_segment(source, func_node)

    st_mod = types.SimpleNamespace(
        cache_data=lambda *a, **k: (lambda f: f),
        error=MagicMock(),
        session_state={},
    )

    module = types.ModuleType('tmp')
    module.pd = pd
    module.requests = requests
    module.io = io
    module.st = st_mod

    exec(func_src, module.__dict__)
    return module, st_mod


def test_load_vocab_sheet_timeout(monkeypatch):
    module, st_mod = _get_vocab_loader()
    monkeypatch.setattr(module.requests, 'get', MagicMock(side_effect=requests.Timeout('boom')))
    df = module._load_full_vocab_sheet_cached()
    assert df.empty
    assert list(df.columns) == ['level', 'german', 'english', 'example']
    st_mod.error.assert_called_once()
    assert 'Could not load vocab sheet' in st_mod.error.call_args[0][0]
