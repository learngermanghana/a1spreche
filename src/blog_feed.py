import csv
from io import StringIO
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
    feed_url = (
        "https://docs.google.com/spreadsheets/"
        "d/1EnVuN1RgSjC0CiBM-I5QVMKhpqgveBO1u6JLmdVhA4A/export?format=csv&gid=0"
    )
    try:
        resp = requests.get(feed_url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []

    try:
        reader = csv.DictReader(StringIO(resp.content.decode("utf-8")))
    except Exception:
        return []

    # Normalize headers to be case-insensitive and whitespace tolerant
    reader.fieldnames = [fn.strip().lower() for fn in reader.fieldnames or []]

    items: List[Dict[str, str]] = []
    for row in reader:
        if len(items) >= min(limit, 5):
            break
        title = (row.get("topic") or "").strip()
        href = (row.get("link") or "").strip()
        if not title or not href:
            continue
        body = (row.get("body") or row.get("description") or "").strip()
        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        items.append(item)
    return items
