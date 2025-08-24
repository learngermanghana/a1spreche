"""YouTube helper functions for Falowen App."""

import requests
import streamlit as st

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


@st.cache_data(ttl=43200)
def fetch_youtube_playlist_videos(
    playlist_id: str, api_key: str = YOUTUBE_API_KEY
) -> list[dict]:
    """Fetch videos for a given YouTube playlist."""
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
    }
    videos, next_page = [], ""
    while True:
        if next_page:
            params["pageToken"] = next_page
        response = requests.get(base_url, params=params, timeout=12)
        data = response.json()
        for item in data.get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            videos.append(
                {
                    "title": item["snippet"]["title"],
                    "url": f"https://www.youtube.com/watch?v={vid}",
                }
            )
        next_page = data.get("nextPageToken")
        if not next_page:
            break
    return videos
