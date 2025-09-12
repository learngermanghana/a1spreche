from typing import List, Dict

import requests
from bs4 import BeautifulSoup
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_blog_feed(limit: int | None = None) -> List[Dict[str, str]]:
    """Fetch and parse the Falowen blog XML feed.

    Parameters
    ----------
    limit: int | None
        Maximum number of recent items to return. ``None`` returns all items.

    Returns
    -------
    List[Dict[str, str]]
        A list of dictionaries each containing ``title``, ``body`` and ``href``.
        Returns an empty list on any error.
    """
    feed_url = "https://blog.falowen.app/feed.xml"
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
    except Exception:
        return []

    raw_items = soup.find_all(["item", "entry"])
    items: List[Dict[str, str]] = []
    for row in raw_items:
        if limit is not None and len(items) >= limit:
            break

        title_tag = row.find("title")
        title = title_tag.text.strip() if title_tag and title_tag.text else ""

        link_tag = row.find("link")
        href = ""
        if link_tag:
            if link_tag.has_attr("href"):
                href = link_tag["href"].strip()
            elif link_tag.text:
                href = link_tag.text.strip()

        if not title or not href:
            continue

        body_tag = (
            row.find("description")
            or row.find("content")
            or row.find("summary")
            or row.find("content:encoded")
        )
        body_html = body_tag.decode_contents() if body_tag and body_tag.text else ""
        body = ""
        if body_html:
            body = BeautifulSoup(body_html, "html.parser").get_text(" ", strip=True)

        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        items.append(item)

    return items
