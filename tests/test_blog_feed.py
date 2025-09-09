import sys
from pathlib import Path
from types import SimpleNamespace

# Allow importing from src
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src import blog_feed


RSS_SNIPPET = """<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0'>
  <channel>
    <item>
      <title>First Post</title>
      <description>Hello World</description>
      <link>https://example.com/1</link>
    </item>
    <item>
      <title>Second Post</title>
      <description>Another</description>
      <link>https://example.com/2</link>
    </item>
  </channel>
</rss>"""


def test_fetch_blog_feed_parses_rss(monkeypatch):
    resp = SimpleNamespace(text=RSS_SNIPPET, raise_for_status=lambda: None)
    monkeypatch.setattr(blog_feed.requests, "get", lambda *_, **__: resp)
    data = blog_feed.fetch_blog_feed("http://test")
    assert data == [
        {
            "title": "First Post",
            "body": "Hello World",
            "href": "https://example.com/1",
        },
        {
            "title": "Second Post",
            "body": "Another",
            "href": "https://example.com/2",
        },
    ]


def test_fetch_blog_feed_network_error(monkeypatch):
    def boom(*_, **__):
        raise blog_feed.requests.RequestException("fail")

    monkeypatch.setattr(blog_feed.requests, "get", boom)
    data = blog_feed.fetch_blog_feed("http://test")
    assert data == blog_feed.FALLBACK


def test_fetch_blog_feed_malformed_feed(monkeypatch):
    resp = SimpleNamespace(text="not xml", raise_for_status=lambda: None)
    monkeypatch.setattr(blog_feed.requests, "get", lambda *_, **__: resp)
    data = blog_feed.fetch_blog_feed("http://test")
    assert data == blog_feed.FALLBACK
