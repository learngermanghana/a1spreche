import sys
from pathlib import Path
import html

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.assignment import linkify_html, _clean_link, _is_http_url

def test_linkify_html_converts_urls() -> None:
    text = "Visit http://example.com for info"
    result = linkify_html(text)
    assert '<a href="http://example.com"' in result
    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer"' in result
    assert html.escape("<b>bold</b>") in linkify_html("<b>bold</b>")


@pytest.mark.parametrize("punct", [".", ",", "!", "?", ";", ":"])
def test_linkify_html_excludes_trailing_punctuation(punct: str) -> None:
    text = f"Visit http://example.com{punct}"
    result = linkify_html(text)
    assert '<a href="http://example.com"' in result
    assert f'href="http://example.com{punct}"' not in result
    assert result.endswith(f'</a>{punct}')

def test_clean_link_and_is_http_url() -> None:
    assert _clean_link(None) == ""
    assert _clean_link(float("nan")) == ""
    assert _clean_link(" nan ") == ""
    assert _clean_link(" https://example.com ") == "https://example.com"
    assert _is_http_url("https://example.com") is True
    assert _is_http_url("ftp://example.com") is False
    assert _is_http_url("not a url") is False
    assert _is_http_url(None) is False
