import sys
from pathlib import Path
import json
import hashlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from streamlit.testing.v1 import AppTest

# Allow importing from src
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src import ui_widgets

BANNER = "www.falowen.app – your German conversational partner"


def test_render_announcements_includes_banner(monkeypatch):
    captured = {}

    def fake_html(html, *_, **__):
        captured["html"] = html

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=fake_html))

    def app():
        from src import ui_widgets as uw
        uw.render_announcements([{"title": "t", "body": "b"}])

    at = AppTest.from_function(app)
    at.run()
    assert BANNER in captured["html"]

def test_render_announcements_fallback_banner(monkeypatch):

    def failing_html(*_, **__):
        raise TypeError("no components")

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=failing_html))

    def app():
        from src import ui_widgets as uw
        uw.render_announcements([{"title": "t", "body": "b"}])

    at = AppTest.from_function(app)
    at.run()
    bodies = [m.body for m in at.markdown]
    assert BANNER in bodies[0]
    assert BANNER in bodies[-1]

def test_render_announcements_empty(monkeypatch):
    called = {}

    def fake_html(*_, **__):
        called["html"] = True

    monkeypatch.setattr(ui_widgets, "components", SimpleNamespace(html=fake_html))

    def app():
        from src import ui_widgets as uw
        uw.render_announcements([])

    at = AppTest.from_function(app)
    at.run()
    assert at.info[0].body == "📣 No new updates to show."
    assert "html" not in called
    assert all(BANNER not in m.body for m in at.markdown)

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
