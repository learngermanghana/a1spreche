import types
import requests

from src.blog_feed import fetch_blog_feed


def test_fetch_blog_feed_maps_title_and_url(monkeypatch):
    json_data = {"items": [{"title": "Test", "url": "http://example.com"}]}

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(json=lambda: json_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["title"] == "Test"
    assert items[0]["href"] == "http://example.com"
    assert "body" not in items[0]


def test_fetch_blog_feed_parses_description(monkeypatch):
    json_data = {
        "items": [
            {
                "title": "Test",
                "url": "http://example.com",
                "summary": "Desc",
            }
        ]
    }

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(json=lambda: json_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["title"] == "Test"
    assert items[0]["href"] == "http://example.com"
    assert items[0]["body"] == "Desc"


def test_fetch_blog_feed_skips_items_missing_fields(monkeypatch):
    json_data = {
        "items": [
            {"title": "Valid", "url": "http://example.com"},
            {"title": "No URL"},
            {"url": "http://example.org"},
            {"title": "Another", "url": "http://example.org"},
        ]
    }

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(json=lambda: json_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=5)
    assert len(items) == 2
    assert items[0]["title"] == "Valid"
    assert items[1]["title"] == "Another"


def test_fetch_blog_feed_handles_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("nope")

    monkeypatch.setattr(requests, "get", boom)
    fetch_blog_feed.clear()
    assert fetch_blog_feed() == []
