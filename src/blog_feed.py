# src/blog_feed.py
# Requires: requests, beautifulsoup4, streamlit

from __future__ import annotations
from typing import List, Dict, Optional
import re

import requests
from bs4 import BeautifulSoup, NavigableString  # type: ignore
import streamlit as st

FEED_URL = "https://blog.falowen.app/feed.xml"

# ----------------------------
# Small cached HTTP helpers
# ----------------------------

@st.cache_data(ttl=60 * 60, show_spinner=False)
def _get(url: str) -> Optional[str]:
    """Cached HTTP GET that returns response text or None."""
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "FalowenDashboard/1.0 (+https://falowen.app)"},
        )
        r.raise_for_status()
        return r.text
    except Exception:
        return None


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def _get_og_meta(page_url: str) -> Dict[str, str]:
    """
    Fetch Open Graph / Twitter meta from an article page.
    Returns a dict that can include 'image' and 'description'.
    """
    html = _get(page_url)
    meta: Dict[str, str] = {}
    if not html:
        return meta
    try:
        s = BeautifulSoup(html, "html.parser")

        def pick(sel: str) -> str:
            t = s.select_one(sel)
            return (t.get("content") or "").strip() if t and t.get("content") else ""

        # Image
        meta["image"] = (
            pick('meta[property="og:image"]')
            or pick('meta[name="twitter:image"]')
            or pick('meta[property="og:image:secure_url"]')
        )

        # Description
        meta["description"] = (
            pick('meta[property="og:description"]')
            or pick('meta[name="description"]')
            or pick('meta[name="twitter:description"]')
        )
    except Exception:
        pass
    return meta


# ----------------------------
# Parsing helpers
# ----------------------------

def _first_img_src_from_html(html: str) -> Optional[str]:
    try:
        s = BeautifulSoup(html, "html.parser")
        img = s.find("img")
        if img:
            src = (img.get("src") or "").strip()
            return src or None
    except Exception:
        return None
    return None


def _prefer_bigger_url(tags) -> Optional[str]:
    """Pick URL from media/enclosure-like tags, preferring larger width*height."""
    picked: Optional[str] = None
    picked_area = -1
    for t in tags:
        url = (t.get("url") or t.get("href") or "").strip()
        if not url:
            continue
        w = t.get("width")
        h = t.get("height")
        try:
            area = (int(w) if w else 0) * (int(h) if h else 0)
        except Exception:
            area = 0
        if area > picked_area:
            picked = url
            picked_area = area
    return picked


# ----------------------------
# Public API
# ----------------------------

@st.cache_data(ttl=60 * 60, show_spinner=False)
def fetch_blog_feed(limit: Optional[int] = None) -> List[Dict[str, str]]:
    """
    Fetch and parse the blog RSS/Atom feed, including thumbnail images.

    Returns a list of items with keys:
      - "title": str
      - "href": str
      - "body"?: str         (plain text; HTML stripped)
      - "image"?: str        (absolute URL)
    """
    text = _get(FEED_URL)
    if not text:
        return []

    # Parse as XML if possible; fall back to HTML parser for lenient parsing
    try:
        soup = BeautifulSoup(text, "xml")
    except Exception:
        soup = BeautifulSoup(text, "html.parser")

    items: List[Dict[str, str]] = []
    for row in soup.find_all(["item", "entry"]):
        if limit is not None and len(items) >= limit:
            break

        # Title
        title_tag = row.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Link (RSS <link>text or Atom <link href="..."> / <link rel="alternate">)
        href = ""
        link_tag = row.find("link")
        if link_tag:
            href = (link_tag.get("href") or link_tag.text or "").strip()
        if not href:
            alt = row.find("link", attrs={"rel": "alternate"})
            if alt:
                href = (alt.get("href") or "").strip()

        if not title or not href:
            # Skip incomplete entries
            continue

        # Body/summary: prefer richer fields first
        body_html = ""
        for tag_name in ("content:encoded", "content", "summary", "description"):
            t = row.find(tag_name)
            if t:
                content = t.decode_contents()
                if content:
                    body_html = content
                    break

        body = ""
        if body_html:
            soup_body = BeautifulSoup(body_html, "html.parser")
            # Drop <style>/<script>
            for t in soup_body(["style", "script"]):
                t.decompose()
            # Remove leading templating noise if present
            for element in list(soup_body.contents):
                if isinstance(element, NavigableString) and "{" in element and "}" in element:
                    element.extract()
                else:
                    break
            # Convert to clean text
            body = soup_body.get_text(" ", strip=True)

        # --- Image detection ---
        image_url: Optional[str] = None

        # 1) media:content / media:thumbnail / media:group
        media_tags = row.find_all(["media:content", "media:thumbnail", "media:group"])
        if media_tags:
            image_url = _prefer_bigger_url(media_tags)

        # 2) <enclosure type="image/*">
        if not image_url:
            for enc in row.find_all("enclosure"):
                if (enc.get("type") or "").startswith("image/"):
                    image_url = (enc.get("url") or "").strip()
                    if image_url:
                        break

        # 3) <image>/<thumbnail>/<figure>
        if not image_url:
            candidates = []
            for name in ("image", "thumbnail", "figure"):
                for t in row.find_all(name):
                    u = (t.get("url") or t.get("href") or t.text or "").strip()
                    if u:
                        candidates.append(u)
            if candidates:
                image_url = candidates[0]

        # 4) First <img> inside body HTML
        if not image_url and body_html:
            image_url = _first_img_src_from_html(body_html)

        # 5) Fallback to OG meta (image + description)
        og_meta: Optional[Dict[str, str]] = None
        if not image_url or not body:
            og_meta = _get_og_meta(href)

        if not image_url and og_meta and og_meta.get("image"):
            image_url = og_meta["image"]

        if not body and og_meta and og_meta.get("description"):
            body = og_meta["description"].strip()

        # Normalize/validate image URL
        if image_url:
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            # accept only http/https
            if not re.match(r"^https?://", image_url, flags=re.I):
                image_url = None

        # Build item
        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        if image_url:
            item["image"] = image_url

        items.append(item)

    return items
