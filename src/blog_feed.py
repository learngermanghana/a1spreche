from __future__ import annotations
from typing import List, Dict, Optional
import re
import requests
from bs4 import BeautifulSoup, NavigableString
import streamlit as st

FEED_URL = "https://blog.falowen.app/feed.xml"


@st.cache_data(ttl=60*60, show_spinner=False)
def _get(url: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "FalowenDashboard/1.0"})
        r.raise_for_status()
        return r.text
    except Exception:
        return None


@st.cache_data(ttl=24*60*60, show_spinner=False)
def _get_og_image(page_url: str) -> Optional[str]:
    html = _get(page_url)
    if not html:
        return None
    try:
        s = BeautifulSoup(html, "html.parser")
        for selector in ['meta[property="og:image"]','meta[name="twitter:image"]','meta[property="og:image:secure_url"]']:
            tag = s.select_one(selector)
            if tag and tag.get("content"):
                return tag.get("content")
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
    picked, picked_area = None, -1
    for t in tags:
        url = (t.get("url") or t.get("href") or "").strip()
        if not url:
            continue
        try:
            area = int(t.get("width") or 0) * int(t.get("height") or 0)
        except Exception:
            area = 0
        if area > picked_area:
            picked, picked_area = url, area
    return picked


@st.cache_data(ttl=60*60, show_spinner=False)
def fetch_blog_feed(limit: Optional[int] = None) -> List[Dict[str, str]]:
    text = _get(FEED_URL)
    if not text:
        return []
    try:
        soup = BeautifulSoup(text, "xml")
    except Exception:
        soup = BeautifulSoup(text, "html.parser")

    items: List[Dict[str, str]] = []
    for row in soup.find_all(["item", "entry"]):
        if limit is not None and len(items) >= limit:
            break

        title_tag = row.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
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

        body_html = ""
        for tag_name in ("description","content:encoded","content","summary"):
            t = row.find(tag_name)
            if t:
                body_html = t.decode_contents()
                if body_html:
                    break

        body = ""
        if body_html:
            soup_body = BeautifulSoup(body_html, "html.parser")
            for t in soup_body(["style","script"]):
                t.decompose()
            for element in list(soup_body.contents):
                if isinstance(element, NavigableString) and "{" in element and "}" in element:
                    element.extract()
                else:
                    break
            body = soup_body.get_text(" ", strip=True)

        image_url: Optional[str] = None
        media_tags = row.find_all(["media:content","media:thumbnail","media:group"])
        if media_tags:
            image_url = _prefer_bigger_url(media_tags)
        if not image_url:
            for enc in row.find_all("enclosure"):
                if (enc.get("type") or "").startswith("image/"):
                    image_url = (enc.get("url") or "").strip()
                    if image_url:
                        break
        if not image_url:
            for name in ("image","thumbnail","figure"):
                for t in row.find_all(name):
                    u = (t.get("url") or t.get("href") or t.text or "").strip()
                    if u:
                        image_url = u
                        break
                if image_url:
                    break
        if not image_url and body_html:
            image_url = _first_img_src_from_html(body_html)
        if not image_url:
            image_url = _get_og_image(href)

        if image_url and image_url.startswith("//"):
            image_url = "https:" + image_url
        if image_url and not re.match(r"^https?://", image_url, flags=re.I):
            image_url = None

        item: Dict[str, str] = {"title": title, "href": href}
        if body:
            item["body"] = body
        if image_url:
            item["image"] = image_url
        items.append(item)

    return items

