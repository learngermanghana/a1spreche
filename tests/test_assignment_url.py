import html
import re
import urllib.parse

import pandas as pd


def linkify_html(text):
    """Escape HTML and convert URLs in plain text to anchor tags."""
    s = "" if text is None or (isinstance(text, float) and pd.isna(text)) else str(text)
    s = html.escape(s)
    s = re.sub(r'(https?://[^\s<]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
    return s


def _clean_link(val) -> str:
    """Return a clean string or '' if empty/NaN/common placeholders."""
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() in {"", "nan", "none", "null", "0"} else s


def _is_http_url(s: str) -> bool:
    try:
        u = urllib.parse.urlparse(str(s))
        return u.scheme in ("http", "https") and bool(u.netloc)
    except Exception:
        return False


def test_linkify_html_converts_urls():
    text = "Visit http://example.com for info"
    result = linkify_html(text)
    assert '<a href="http://example.com"' in result
    assert 'target="_blank"' in result
    assert html.escape("<b>bold</b>") in linkify_html("<b>bold</b>")


def test_clean_link_and_is_http_url():
    assert _clean_link(None) == ""
    assert _clean_link(" nan ") == ""
    assert _clean_link(" https://example.com ") == "https://example.com"
    assert _is_http_url("https://example.com") is True
    assert _is_http_url("ftp://example.com") is False
    assert _is_http_url("not a url") is False
