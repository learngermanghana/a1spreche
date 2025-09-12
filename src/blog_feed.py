from __future__ import annotations
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup, NavigableString
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_blog_feed(limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Fetch and parse the Falowen blog XML/Atom feed.

    Parameters
    ----------
    limit: Optional[int]
        Maximum number of recent items to return. ``None`` returns all items.

    Returns
    -------
    List[Dict[str, str]]
        A list of dictionaries each containing ``title``, ``href`` and optionally ``body``.
        Returns an empty list on any error.
    """
    feed_url = "https://blog.falowen.app/feed.xml"
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    # Try to parse as XML; fall back to HTML if needed (some feeds serve as text/html)
    try:
        soup = BeautifulSoup(resp.text, "xml")
    except Exception:
        soup = BeautifulSoup(resp.text, "html.parser")  # graceful fallback

    raw_items = soup.find_all(["item", "entry"])  # RSS <item> or Atom <entry>
    items: List[Dict[str, str]] = []
    for row in raw_items:
        if limit is not None and len(items) >= limit:
            break

        # Title
        title = (row.find_text("title") or "").strip()

        # Link (Atom often uses <link rel="alternate" href="..."/>)
        href = ""
        link_tag = row.find("link")
        if link_tag:
            href = (link_tag.get("href") or link_tag.text or "").strip()
        if not href:
            alt = row.find("link", attrs={"rel": "alternate"})
            if alt:
                href = (alt.get("href") or "").strip()

        if not title or not href:
            continue

        # Body/summary
        body_html = ""
        for tag_name in ("description", "content:encoded", "content", "summary"):
            t = row.find(tag_name)
            if t:
                # prefer raw inner HTML if present
                body_html = t.decode_contents() if t.text else ""
                if body_html:
                    break

        body = ""
        if body_html:
            soup_body = BeautifulSoup(body_html, "html.parser")
            # Drop <style>/<script>
            for t in soup_body(["style", "script"]):
                t.decompose()
            # Remove leading Liquid/Twig-like braces if present
            for element in list(soup_body.contents):
                if isinstance(element, NavigableString) and "{" in element and "}" in element:
                    element.extract()
                else:
                    break
            body = soup_body.get_text(" ", strip=True)

        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        items.append(item)

    return items
