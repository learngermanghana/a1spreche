import sys
from pathlib import Path
import json
import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock

from streamlit.testing.v1 import AppTest

# Allow importing from src
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src import ui_widgets

BANNER = "www.falowen.app – your German conversational partner"
HEADING = "📣 Falowen blog updates"


def test_render_announcements_without_banner(monkeypatch):
    import importlib
    importlib.reload(ui_widgets)
    captured = {}

    def fake_html(html, *_, **__):
        captured["html"] = html

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=fake_html))
    ui_widgets.render_announcements([
        {"title": "t", "body": "b", "href": "https://xmpl"},
        {"title": "t2"},
    ])
    assert HEADING in captured["html"]
    assert "Falowen: Your German Conversation Partner for Everyday Learning" in captured["html"]
    assert "t" in captured["html"]
    assert "b" in captured["html"]
    assert "Read more" in captured["html"]
    assert "setInterval" in captured["html"]
    assert BANNER not in captured["html"]


def test_render_announcements_fallback_without_banner(monkeypatch):
    import importlib
    importlib.reload(ui_widgets)
    outputs = []

    def failing_html(*_, **__):
        raise TypeError("no components")

    def fake_markdown(msg, *_, **__):
        outputs.append(msg)

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=failing_html))
    monkeypatch.setattr(ui_widgets.st, "markdown", fake_markdown)
    ui_widgets.render_announcements(
        [{"title": "t", "body": "b", "href": "https://xmpl"}]
    )
    assert outputs == [
        "[**t**](https://xmpl) — b",
        "Visit [blog.falowen.app](https://blog.falowen.app) for more.",
    ]
    assert all(BANNER not in o for o in outputs)


def test_render_announcements_empty(monkeypatch):
    import importlib
    importlib.reload(ui_widgets)
    info_msgs = []
    called = {}

    def fake_html(*_, **__):
        called["html"] = True

    def fake_info(msg, *_, **__):
        info_msgs.append(msg)

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=fake_html))
    monkeypatch.setattr(ui_widgets.st, "info", fake_info)
    ui_widgets.render_announcements([])
    assert info_msgs == ["📣 No new updates to show."]
    assert "html" not in called
    assert all(BANNER not in m for m in info_msgs)


def test_render_announcements_footer_has_blog_link(monkeypatch):
    import importlib
    importlib.reload(ui_widgets)
    footers = []

    def fake_html(*_, **__):
        return None

    def fake_markdown(msg, *_, **__):
        footers.append(msg)

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=fake_html))
    monkeypatch.setattr(ui_widgets.st, "markdown", fake_markdown)
    ui_widgets.render_announcements([{"title": "t"}])
    assert footers == ["Visit [blog.falowen.app](https://blog.falowen.app) for more."]

def test_render_announcements_once_skips_when_hash_matches(monkeypatch):
    render_mock = MagicMock()
    monkeypatch.setattr(ui_widgets, "render_announcements", render_mock)

    def app():
        import streamlit as st
        from src import ui_widgets as uw
        data = [{"title": "t", "body": "b"}]
        hash_val = hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()
        st.session_state["_ann_hash"] = hash_val
        uw.render_announcements_once(data, dashboard_active=False)

    at = AppTest.from_function(app)
    at.run()
    render_mock.assert_not_called()
