from __future__ import annotations
from typing import List, Dict, Optional
import re

import requests
from bs4 import BeautifulSoup, NavigableString  # type: ignore
import streamlit as st


FEED_URL = "https://blog.falowen.app/feed.xml"


@st.cache_data(ttl=60 * 60, show_spinner=False)
def _get(url: str) -> Optional[str]:
    """Small cached GET to reduce network churn."""
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "FalowenDashboard/1.0"})
        r.raise_for_status()
        return r.text
    except Exception:
        return None


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def _get_og_image(page_url: str) -> Optional[str]:
    """Try to fetch Open Graph / Twitter image from an article page."""
    html = _get(page_url)
    if not html:
        return None
    try:
        s = BeautifulSoup(html, "html.parser")
        # Preference order: og:image, twitter:image, og:image:secure_url
        for selector, attr in [
            ('meta[property="og:image"]', "content"),
            ('meta[name="twitter:image"]', "content"),
            ('meta[property="og:image:secure_url"]', "content"),
        ]:
            tag = s.select_one(selector)
            if tag and tag.get(attr):
                return tag.get(attr)  # type: ignore[return-value]
    except Exception:
        return None
    return None


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
    """Pick URL from a list of media/enclosure-like tags, prefer with size hints."""
    picked = None
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


@st.cache_data(ttl=60 * 60, show_spinner=False)
def fetch_blog_feed(limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Fetch and parse the blog XML/Atom feed, including thumbnail images.

    Returns items with keys: title, href, (optional) body, (optional) image.
    """
    text = _get(FEED_URL)
    if not text:
        return []

    # Try strict XML first, fall back to permissive HTML parser.
    try:
        soup = BeautifulSoup(text, "xml")
    except Exception:
        soup = BeautifulSoup(text, "html.parser")

    raw_items = soup.find_all(["item", "entry"])
    items: List[Dict[str, str]] = []
    for row in raw_items:
        if limit is not None and len(items) >= limit:
            break

        # Title
        title_tag = row.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Link (RSS <link> text, Atom <link href="..."> or <link rel="alternate" ...>)
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
                # Use inner HTML if available
                content = t.decode_contents() if t else ""
                if content:
                    body_html = content
                    break

        body = ""
        if body_html:
            soup_body = BeautifulSoup(body_html, "html.parser")
            # Drop <style>/<script>
            for t in soup_body(["style", "script"]):
                t.decompose()
            # Remove leading templating noise
            for element in list(soup_body.contents):
                if isinstance(element, NavigableString) and "{" in element and "}" in element:
                    element.extract()
                else:
                    break
            # Convert to clean text
            body = soup_body.get_text(" ", strip=True)

        # --- Image detection ---
        image_url: Optional[str] = None

        # 1) media:content or media:thumbnail (YouTube/WordPress etc.)
        media_tags = row.find_all(["media:content", "media:thumbnail", "media:group"])
        if media_tags:
            image_url = _prefer_bigger_url(media_tags)

        # 2) enclosure with image type
        if not image_url:
            for enc in row.find_all("enclosure"):
                if (enc.get("type") or "").startswith("image/"):
                    image_url = (enc.get("url") or "").strip()
                    if image_url:
                        break

        # 3) <image>, <thumbnail>, or custom
        if not image_url:
            candidates = []
            for name in ("image", "thumbnail", "figure"):
                for t in row.find_all(name):
                    u = (t.get("url") or t.get("href") or t.text or "").strip()
                    if u:
                        candidates.append(u)
            if candidates:
                image_url = candidates[0]

        # 4) First <img> in body HTML
        if not image_url and body_html:
            image_url = _first_img_src_from_html(body_html)

        # 5) Fallback: fetch OG image from article page (best-effort)
        if not image_url:
            image_url = _get_og_image(href)

        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        if image_url:
            # Resolve protocol-relative //... to https
            if image_url.startswith("//"):
                image_url = "https:" + image_url
            # Basic sanitization (no data: URIs)
            if not re.match(r"^https?://", image_url, flags=re.I):
                image_url = None
        if image_url:
            item["image"] = image_url

        items.append(item)

    return items
