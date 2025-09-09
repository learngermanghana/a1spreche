import xml.etree.ElementTree as ET
from typing import List, Dict

import requests
import streamlit as st


@st.cache_data(ttl=3600)
def fetch_blog_feed(limit: int = 5) -> List[Dict[str, str]]:
    """Fetch and parse the Falowen blog feed.

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
    feed_url = "https://blog.falowen.app/feed.xml"
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        return []

    items: List[Dict[str, str]] = []
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }

    if root.tag.endswith("feed"):
        entries = root.findall("atom:entry", ns)
        for entry in entries[:limit]:
            title_el = entry.find("atom:title", ns)
            content_el = entry.find("atom:content", ns) or entry.find("atom:summary", ns)
            link_el = entry.find("atom:link", ns)
            items.append(
                {
                    "title": title_el.text if title_el is not None else "",
                    "body": content_el.text if content_el is not None else "",
                    "href": link_el.get("href") if link_el is not None else None,
                }
            )
    else:
        channel = root.find("channel")
        if channel is None:
            return []
        for entry in channel.findall("item")[:limit]:
            title_el = entry.find("title")
            link_el = entry.find("link")
            desc_el = entry.find("description")
            content_el = entry.find("content:encoded", ns)
            body = ""
            if content_el is not None and content_el.text:
                body = content_el.text
            elif desc_el is not None and desc_el.text:
                body = desc_el.text
            items.append(
                {
                    "title": title_el.text if title_el is not None else "",
                    "body": body,
                    "href": link_el.text if link_el is not None else None,
                }
            )
    return items
