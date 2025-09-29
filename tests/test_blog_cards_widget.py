from src.blog_cards_widget import render_blog_cards


def test_render_blog_cards_sanitizes_links(monkeypatch):
    captured = {}

    def fake_html(html_block, height=None, scrolling=False):
        captured["html"] = html_block

    monkeypatch.setattr("src.blog_cards_widget.components.html", fake_html)

    items = [
        {
            "title": "Unsafe Link",
            "href": "javascript:alert('oops')",
            "body": "<p>Body</p>",
        },
        {
            "title": "Data Link",
            "href": "data:text/html;base64,PHNjcmlwdD4=",
            "body": "<p>Another Body</p>",
        },
    ]

    render_blog_cards(items, height=200)

    html = captured.get("html", "")
    assert "javascript:" not in html
    assert "data:" not in html
    assert 'href="#"' in html
