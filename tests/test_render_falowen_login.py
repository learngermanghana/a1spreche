import ast
import pathlib
import types
from unittest.mock import MagicMock

import pytest


def load_login_module():
    path = pathlib.Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = path.read_text()
    module_ast = ast.parse(source)
    nodes = []
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name in {"_load_falowen_login_html", "render_falowen_login"}:
            nodes.append(node)
    mod = types.ModuleType("login_module")
    mod.Path = pathlib.Path
    mod.re = __import__("re")
    mod.lru_cache = __import__("functools").lru_cache
    mod.st = MagicMock()
    mod.st.error = MagicMock()
    mod.components = MagicMock()
    code = compile(ast.Module(body=nodes, type_ignores=[]), "login_module", "exec")
    exec(code, mod.__dict__)
    return mod


@pytest.fixture()
def login_mod():
    mod = load_login_module()
    assert hasattr(mod, "render_falowen_login"), "render_falowen_login not defined"
    return mod


def test_render_calls_components_html(login_mod, monkeypatch):
    sample_html = """
<!-- Right: Login -->
<aside>legacy</aside>
<div style=\"grid-template-columns:1.2fr .8fr;\">X</div>
<script>bad</script></body>
"""
    monkeypatch.setattr(pathlib.Path, "read_text", lambda self, encoding='utf-8': sample_html)
    login_mod._load_falowen_login_html.cache_clear()
    expected_html = login_mod._load_falowen_login_html()
    login_mod.components.html.reset_mock()
    login_mod.render_falowen_login("auth_url")
    login_mod.components.html.assert_called_once_with(expected_html, height=720, scrolling=True, key="falowen_hero")


def test_missing_template_shows_error(login_mod, monkeypatch):
    monkeypatch.setattr(pathlib.Path, "read_text", MagicMock(side_effect=FileNotFoundError))
    login_mod._load_falowen_login_html.cache_clear()
    login_mod.render_falowen_login("auth_url")
    login_mod.st.error.assert_called_once()
    assert not login_mod.components.html.called
