import types

import requests

from src.blog_feed import fetch_blog_feed


def test_fetch_blog_feed_parses_items(monkeypatch):
    sample = "Topic,Link,Body\nTest,http://example.com,Hello\n" "Another,http://ex.com,"

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(content=sample.encode(), raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items == [{"title": "Test", "href": "http://example.com", "body": "Hello"}]


def test_fetch_blog_feed_handles_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("nope")

    monkeypatch.setattr(requests, "get", boom)
    fetch_blog_feed.clear()
    assert fetch_blog_feed() == []
