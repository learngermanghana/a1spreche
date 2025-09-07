from pathlib import Path

from src.ui.login import load_falowen_login_html


def test_loads_real_template(monkeypatch):
    """Ensure the real Falowen login template is used."""
    # Use repository root as working directory so the function resolves the real template path
    repo_root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(repo_root)

    load_falowen_login_html.cache_clear()
    html = load_falowen_login_html()

    assert "<h1>Falowen</h1>" in html
    assert "Welcome to Falowen" in html
    assert "class=\"features\"" in html
