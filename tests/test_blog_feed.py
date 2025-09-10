import types

import requests

from src.blog_feed import fetch_blog_feed


def test_fetch_blog_feed_maps_topic_and_link(monkeypatch):
    csv_data = "Topic,Link\nTest,http://example.com\n"

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(content=csv_data.encode("utf-8"), raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["title"] == "Test"
    assert items[0]["href"] == "http://example.com"
    assert "body" not in items[0]


def test_fetch_blog_feed_handles_lowercase_headers(monkeypatch):
    csv_data = "topic,link,body\nTest,http://example.com,Desc\n"

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(content=csv_data.encode("utf-8"), raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["title"] == "Test"
    assert items[0]["href"] == "http://example.com"
    assert items[0]["body"] == "Desc"


def test_fetch_blog_feed_skips_empty_rows(monkeypatch):
    csv_data = "Topic,Link\nValid,http://example.com\n,\nAnother,http://example.org\n"

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(content=csv_data.encode("utf-8"), raise_for_status=lambda: None)

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
