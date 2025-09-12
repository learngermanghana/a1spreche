from typing import List, Dict

import requests
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_blog_feed(limit: int = 5) -> List[Dict[str, str]]:
    """Fetch and parse the Falowen blog JSON feed.

    Parameters
    ----------
    limit: int
        Maximum number of recent items to return.

    Returns
    -------
    List[Dict[str, str]]
        A list of dictionaries each containing ``title``, ``body`` and ``href``.
        Returns an empty list on any error.
    """
    feed_url = "https://blog.falowen.app/feed.json"
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    raw_items = data.get("items") if isinstance(data, dict) else []
    if not isinstance(raw_items, list):
        return []

    items: List[Dict[str, str]] = []
    for row in raw_items:
        if len(items) >= min(limit, 5):
            break
        title = (row.get("title") or "").strip()
        href = (
            row.get("url")
            or row.get("external_url")
            or row.get("link")
            or row.get("href")
            or ""
        ).strip()
        if not title or not href:
            continue
        body = (
            row.get("content_text")
            or row.get("content_html")
            or row.get("summary")
            or row.get("description")
            or ""
        )
        body = body.strip() if isinstance(body, str) else ""
        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        items.append(item)
    return items
