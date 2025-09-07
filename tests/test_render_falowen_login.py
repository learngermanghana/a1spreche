import pathlib
import sys
import importlib
import types
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def login_mod(monkeypatch):
    st_mod = types.ModuleType("streamlit")
    st_mod.secrets = {}
    st_mod.session_state = {}
    st_mod.error = MagicMock()
    components_v1 = MagicMock()
    components_mod = types.ModuleType("streamlit.components")
    components_mod.v1 = components_v1
    monkeypatch.setitem(sys.modules, "streamlit", st_mod)
    monkeypatch.setitem(sys.modules, "streamlit.components", components_mod)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", components_v1)
    uiw = importlib.import_module("src.ui_widgets")
    monkeypatch.setattr(uiw, "st", st_mod)
    monkeypatch.setattr(uiw, "components", components_v1)
    mod = importlib.reload(importlib.import_module("src.ui.login"))
    mod.st = st_mod
    mod.components = components_v1
    mod.ui_widgets = uiw
    return mod


def test_render_calls_components_html(login_mod, monkeypatch):
    sample_html = """
<!-- Right: Login -->
<aside>legacy</aside>
<div style=\"grid-template-columns:1.2fr .8fr;\">X</div>
<script>bad</script></body>
"""
    monkeypatch.setattr(pathlib.Path, "read_text", lambda self, encoding='utf-8': sample_html)
    login_mod.load_falowen_login_html.cache_clear()
    expected_html = login_mod.load_falowen_login_html()
    login_mod.components.html.reset_mock()
    login_mod.render_falowen_login()
    login_mod.components.html.assert_called_once_with(expected_html, height=720, scrolling=True)


def test_load_html_removes_multiple_scripts(login_mod, monkeypatch):
    sample_html = """
<!-- Right: Login -->
<aside>legacy</aside>
<script>one</script>
<div style=\"grid-template-columns:1.2fr .8fr;\">X</div>
<script>two</script></body>
"""
    monkeypatch.setattr(pathlib.Path, "read_text", lambda self, encoding='utf-8': sample_html)
    login_mod.load_falowen_login_html.cache_clear()
    cleaned = login_mod.load_falowen_login_html()
    assert "<script" not in cleaned
    assert cleaned.count("</body>") == 1


def test_missing_template_shows_error(login_mod, monkeypatch):
    monkeypatch.setattr(pathlib.Path, "read_text", MagicMock(side_effect=FileNotFoundError))
    login_mod.load_falowen_login_html.cache_clear()
    login_mod.render_falowen_login()
    login_mod.st.error.assert_called_once()
    assert not login_mod.components.html.called


def test_unicode_decode_error_raises_runtime_error(login_mod, monkeypatch):
    err = UnicodeDecodeError("utf-8", b"", 0, 1, "bad data")
    monkeypatch.setattr(pathlib.Path, "read_text", MagicMock(side_effect=err))
    login_mod.load_falowen_login_html.cache_clear()
    with pytest.raises(RuntimeError, match="valid UTF-8"):
        login_mod.load_falowen_login_html()


def test_google_button_injected_when_requested(login_mod, monkeypatch):
    sample_html = (
        '<section class="hero card" data-animate>'
        '<h2>Welcome</h2>'
        '<p class="cta">👇 Scroll to sign in or create your account.</p>'
        '<div class="features"></div>'
        '</section>'
    )
    monkeypatch.setattr(pathlib.Path, "read_text", lambda self, encoding="utf-8": sample_html)
    login_mod.load_falowen_login_html.cache_clear()

    captured = {}
    login_mod.components.html = MagicMock(side_effect=lambda html, **kw: captured.update({"html": html}))

    monkeypatch.setattr(
        login_mod.ui_widgets,
        "render_google_signin_once",
        MagicMock(wraps=login_mod.ui_widgets.render_google_signin_once),
    )
    login_mod.render_falowen_login("https://auth.example", show_google_in_hero=True)

    login_mod.ui_widgets.render_google_signin_once.assert_called_once_with(
        "https://auth.example", full_width=True
    )
    out = captured.get("html", "")
    assert "Continue with Google" in out
    cta = out.index("create your account.")
    btn = out.index("Continue with Google")
    features = out.index('<div class="features">')
    assert cta < btn < features
