"""YouTube playlist utilities."""
from __future__ import annotations

import logging
import textwrap
from typing import List, Optional

import requests
import streamlit as st

DEFAULT_PLAYLIST_LEVEL = "A1"

YOUTUBE_API_KEY = st.secrets.get(
    "YOUTUBE_API_KEY", "AIzaSyBA3nJi6dh6-rmOLkA4Bb0d7h0tLAp7xE4"
)

YOUTUBE_PLAYLIST_IDS = {
    "A1": ["PL5vnwpT4NVTdwFarD9kwm1HONsqQ11l-b"],
    "A2": [
        "PLs7zUO7VPyJ7YxTq_g2Rcl3Jthd5bpTdY",
        "PLquImyRfMt6dVHL4MxFXMILrFh86H_HAc",
        "PLs7zUO7VPyJ5Eg0NOtF9g-RhqA25v385c",
    ],
    "B1": ["PLs7zUO7VPyJ5razSfhOUVbTv9q6SAuPx-", "PLB92CD6B288E5DB61"],
    "B2": [
        "PLs7zUO7VPyJ5XMfT7pLvweRx6kHVgP_9C",
        "PLs7zUO7VPyJ6jZP-s6dlkINuEjFPvKMG0",
        "PLs7zUO7VPyJ4SMosRdB-35Q07brhnVToY",
    ],
}


def get_playlist_ids_for_level(level: str) -> List[str]:
    """Return playlist IDs for a CEFR level with a fallback."""
    level_key = (level or "").strip().upper()
    playlist_ids = YOUTUBE_PLAYLIST_IDS.get(level_key, [])
    if playlist_ids:
        return playlist_ids
    fallback = YOUTUBE_PLAYLIST_IDS.get(DEFAULT_PLAYLIST_LEVEL, [])
    if fallback:
        st.info(
            f"No playlist found for level {level_key}; using {DEFAULT_PLAYLIST_LEVEL} playlist instead."
        )
        return fallback
    st.info(f"No playlist configured for level {level_key}.")
    return []


def _shorten_description(raw: Optional[str], *, max_chars: int = 200) -> Optional[str]:
    """Return a concise, single-line description."""
    if not raw:
        return None
    cleaned = " ".join(raw.split())
    if not cleaned:
        return None
    if len(cleaned) <= max_chars:
        return cleaned
    return textwrap.shorten(cleaned, width=max_chars, placeholder="…")


@st.cache_data(ttl=43200)
def fetch_youtube_playlist_videos(
    playlist_id: str, api_key: str = YOUTUBE_API_KEY
) -> List[dict]:
    """Fetch videos for a given YouTube playlist."""
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
    }
    videos: List[dict] = []
    next_page = ""
    while True:
        if next_page:
            params["pageToken"] = next_page
        try:
            response = requests.get(base_url, params=params, timeout=12)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.exception("Could not fetch YouTube playlist")
            st.error(f"❌ Could not fetch YouTube playlist. {e}")
            raise
        data = response.json()
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            vid = snippet.get("resourceId", {}).get("videoId")
            if not vid:
                continue
            videos.append(
                {
                    "title": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "description": _shorten_description(snippet.get("description")),
                }
            )
        next_page = data.get("nextPageToken")
        if not next_page:
            break
    return videos
