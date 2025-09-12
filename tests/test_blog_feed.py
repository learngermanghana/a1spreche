import types
import requests

from src.blog_feed import fetch_blog_feed


def test_fetch_blog_feed_maps_title_and_url(monkeypatch):
    xml_data = """
    <rss><channel>
      <item>
        <title>Test</title>
        <link>http://example.com</link>
      </item>
    </channel></rss>
    """

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(text=xml_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["title"] == "Test"
    assert items[0]["href"] == "http://example.com"
    assert "body" not in items[0]


def test_fetch_blog_feed_parses_description(monkeypatch):
    xml_data = """
    <rss><channel>
      <item>
        <title>Test</title>
        <link>http://example.com</link>
        <description>Desc</description>
      </item>
    </channel></rss>
    """

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(text=xml_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["title"] == "Test"
    assert items[0]["href"] == "http://example.com"
    assert items[0]["body"] == "Desc"


def test_fetch_blog_feed_skips_items_missing_fields(monkeypatch):
    xml_data = """
    <rss><channel>
      <item><title>Valid</title><link>http://example.com</link></item>
      <item><title>No URL</title></item>
      <item><link>http://example.org</link></item>
      <item><title>Another</title><link>http://example.org</link></item>
    </channel></rss>
    """

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(text=xml_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed()
    assert len(items) == 2
    assert items[0]["title"] == "Valid"
    assert items[1]["title"] == "Another"


def test_fetch_blog_feed_no_limit(monkeypatch):
    xml_items = "".join(
        f"<item><title>T{i}</title><link>http://example.com/{i}</link></item>" for i in range(7)
    )
    xml_data = f"<rss><channel>{xml_items}</channel></rss>"

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(text=xml_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed()
    assert len(items) == 7


def test_fetch_blog_feed_handles_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("nope")

    monkeypatch.setattr(requests, "get", boom)
    fetch_blog_feed.clear()
    assert fetch_blog_feed() == []


def test_fetch_blog_feed_strips_html(monkeypatch):
    xml_data = """
    <rss><channel>
      <item>
        <title>T</title>
        <link>http://example.com</link>
        <description>p{color:red} body{margin:0}<p>Hello <b>World</b><style>p{color:red}</style><script>alert(1)</script>!</p></description>
      </item>
    </channel></rss>
    """

    def fake_get(url, timeout=10):
        return types.SimpleNamespace(text=xml_data, raise_for_status=lambda: None)

    monkeypatch.setattr(requests, "get", fake_get)
    fetch_blog_feed.clear()
    items = fetch_blog_feed(limit=1)
    assert items[0]["body"] == "Hello World !"
    assert "p{color:red}" not in items[0]["body"]
    assert "alert" not in items[0]["body"]
