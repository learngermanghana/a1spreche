from __future__ import annotations

import requests
from xml.etree import ElementTree as ET

# RSS feed URL is configurable for testing.
BLOG_FEED_URL = "https://www.falowen.app/rss"

# Fallback announcements if the feed cannot be loaded.
FALLBACK = [
    {
        "title": "Quick Access Menu",
        "body": "Use the left sidebar for quick access to lessons, tools, and resources.",
        "href": "",
    },
    {
        "title": "Download Receipts & Results",
        "body": "Grab your receipt, results, and enrollment letter under **My Results & Resources**.",
        "href": "",
    },
    {
        "title": "Account Deletion Requests",
        "body": "You can now request account deletion from your account settings.",
        "href": "",
    },
    {
        "title": "Refresh Session Fix",
        "body": "Frequent refresh session prompts have been resolved for smoother navigation.",
        "href": "",
    },
    {
        "title": "Attendance Now Being Marked",
        "body": "Find attendance under My Course ➜ Classroom/Attendance. Telegram notifications are available.",
        "href": "",
    },
]


def _parse_rss(xml: str) -> list[dict]:
    """Parse a minimal RSS feed into announcement dictionaries."""
    root = ET.fromstring(xml)
    items: list[dict] = []
    for item in root.findall(".//item"):
        title = item.findtext("title", default="")
        body = item.findtext("description", default="")
        href = item.findtext("link", default="")
        items.append({"title": title, "body": body, "href": href})
    return items


def fetch_blog_feed(url: str = BLOG_FEED_URL) -> list[dict]:
    """Fetch and parse the blog RSS feed.

    Returns a list of dictionaries with ``title``, ``body`` and ``href`` keys.
    If the network request fails or the feed cannot be parsed, a static
    fallback list is returned instead.
    """
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
    except requests.RequestException:
        return FALLBACK.copy()
    try:
        parsed = _parse_rss(resp.text)
    except Exception:
        return FALLBACK.copy()
    return parsed or FALLBACK.copy()
