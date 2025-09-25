import ast
from pathlib import Path


def test_entrypoint_defines_login_page():
    source = Path('a1sprechen.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    assert any(isinstance(n, ast.FunctionDef) and n.name == 'login_page' for n in tree.body)
