import ast
import types
from pathlib import Path
from unittest.mock import MagicMock


class DummyCtx:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


def load_func(name):
    src = Path("a1sprechen.py").read_text()
    module = ast.parse(src, filename="a1sprechen.py")
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
    code = compile(ast.Module(body=[node], type_ignores=[]), filename=name, mode="exec")
    ns = {}
    exec(code, ns)
    return ns[name], ns


def make_stub_state():
    def markdown(*a, **k):
        return None

    def columns(spec, *a, **k):
        n = spec if isinstance(spec, int) else len(spec)
        return [DummyCtx() for _ in range(n)]

    st = types.SimpleNamespace(
        session_state={
            "logged_in": True,
            "student_code": "SC",
            "student_name": "Name",
            "student_level": "",
        },
        query_params={},
        markdown=markdown,
        info=lambda *a, **k: None,
        tabs=lambda labels: [DummyCtx() for _ in labels],
        columns=columns,
        divider=lambda: None,
        container=lambda: DummyCtx(),
        stop=lambda: None,
    )
    return st


def test_login_page_invokes_topbar_when_logged_in():
    login_page, ns = load_func("login_page")
    st = make_stub_state()
    topbar = MagicMock()
    ensure_mock = MagicMock()
    ns.update(
        {
            "st": st,
            "render_logged_in_topbar": topbar,
            "bootstrap_state": MagicMock(),
            "seed_falowen_state_from_qp": MagicMock(),
            "bootstrap_session_from_qp": MagicMock(),
            "ensure_student_level": ensure_mock,
            "renew_session_if_needed": MagicMock(),
            "render_google_oauth": MagicMock(return_value=""),
            "render_falowen_login": MagicMock(),
            "render_returning_login_area": MagicMock(return_value=False),
            "render_google_brand_button_once": MagicMock(),
            "render_signup_request_banner": MagicMock(),
            "render_signup_form": MagicMock(),
            "fetch_blog_feed": MagicMock(return_value=[]),
            "render_blog_cards": MagicMock(),
        }
    )
    login_page.__globals__.update(ns)
    login_page()
    topbar.assert_called_once()
    ensure_mock.assert_called_once()


def test_dashboard_page_invokes_topbar_when_logged_in():
    dashboard_page, ns = load_func("dashboard_page")
    st = make_stub_state()
    topbar = MagicMock()
    ensure_mock = MagicMock()
    ns.update(
        {
            "st": st,
            "render_logged_in_topbar": topbar,
            "bootstrap_state": MagicMock(),
            "seed_falowen_state_from_qp": MagicMock(),
            "bootstrap_session_from_qp": MagicMock(),
            "ensure_student_level": ensure_mock,
            "login_page": MagicMock(),
            "reset_password_page": MagicMock(),
            "inject_notice_css": MagicMock(),
            "render_sidebar_published": MagicMock(),
            "_maybe_rerun": MagicMock(),
        }
    )
    dashboard_page.__globals__.update(ns)
    dashboard_page()
    topbar.assert_called_once()
    ensure_mock.assert_called_once()

