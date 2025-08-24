import sys
from pathlib import Path
import html

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.assignment import linkify_html, _clean_link, _is_http_url

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
