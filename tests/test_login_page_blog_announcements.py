import ast
import types
from pathlib import Path
from unittest.mock import MagicMock


class DummyCtx:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


def load_login_page():
    src = Path("a1sprechen.py").read_text()
    module = ast.parse(src, filename="a1sprechen.py")
    login_node = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "login_page"
    )
    code = compile(ast.Module(body=[login_node], type_ignores=[]), filename="login_page", mode="exec")
    ns = {}
    exec(code, ns)
    return ns["login_page"], ns


def make_streamlit_stub():
    outputs = []

    def markdown(text, *args, **kwargs):
        outputs.append(text)

    def columns(spec, *args, **kwargs):
        n = spec if isinstance(spec, int) else len(spec)
        return [DummyCtx() for _ in range(n)]

    st = types.SimpleNamespace(
        session_state={},
        markdown=markdown,
        info=lambda *a, **k: None,
        tabs=lambda labels: (DummyCtx(), DummyCtx()),
        columns=columns,
        divider=lambda: None,
        container=lambda: DummyCtx(),
    )
    return st, outputs


def test_login_page_renders_blog_cards_and_link():
    login_page, ns = load_login_page()
    st, outputs = make_streamlit_stub()
    posts = [{"title": f"title-{i}", "href": f"u{i}"} for i in range(5)]
    fetch_mock = MagicMock(return_value=posts)
    render_cards_mock = MagicMock()
    ns.update(
        {
            "st": st,
            "render_google_oauth": MagicMock(return_value="auth"),
            "render_falowen_login": MagicMock(),
            "render_returning_login_area": MagicMock(return_value=False),
            "render_signup_request_banner": MagicMock(),
            "render_signup_form": MagicMock(),
            "render_google_brand_button_once": MagicMock(),
            "fetch_blog_feed": fetch_mock,
            "render_blog_cards": render_cards_mock,
        }
    )
    login_page.__globals__.update(ns)
    login_page()
    fetch_mock.assert_called_once()
    render_cards_mock.assert_called_once()
    assert render_cards_mock.call_args[0][0] == posts[:3]
    assert any("Falowen Blog" in o for o in outputs)
    assert any("Read more" in o for o in outputs)

