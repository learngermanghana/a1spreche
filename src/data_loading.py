"""Data loading helpers for a1sprechen."""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

# ------------------------------------------------------------------------------
# YouTube configuration and helpers
# ------------------------------------------------------------------------------

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


@st.cache_data(ttl=3600)
def fetch_youtube_playlist_videos(
    playlist_id: str, api_key: str = YOUTUBE_API_KEY
) -> List[Dict[str, Any]]:
    """Fetch videos for a given YouTube playlist."""
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": api_key,
    }
    videos: List[Dict[str, Any]] = []
    next_page = ""
    while True:
        if next_page:
            params["pageToken"] = next_page
        response = requests.get(base_url, params=params, timeout=12)
        data = response.json()
        for item in data.get("items", []):
            vid = item["snippet"]["resourceId"]["videoId"]
            videos.append(
                {"title": item["snippet"]["title"], "url": f"https://www.youtube.com/watch?v={vid}"}
            )
        next_page = data.get("nextPageToken")
        if not next_page:
            break
    return videos


# ------------------------------------------------------------------------------
# Student roster loading
# ------------------------------------------------------------------------------

GOOGLE_SHEET_CSV = (
    "https://docs.google.com/spreadsheets/d/12NXf5FeVHr7JJT47mRHh7Jp-TC1yhPS7ZG6nzZVTt1U/"
    "gviz/tq?tqx=out:csv&sheet=Sheet1"
)


@st.cache_data(ttl=300)
def _load_student_data_cached() -> Optional[pd.DataFrame]:
    try:
        resp = requests.get(GOOGLE_SHEET_CSV, timeout=12)
        resp.raise_for_status()
        txt = resp.text
        if "<html" in txt[:512].lower():
            raise ValueError("Expected CSV, got HTML (check sheet privacy).")
        df = pd.read_csv(
            io.StringIO(txt),
            dtype=str,
            keep_default_na=True,
            na_values=["", " ", "nan", "NaN", "None"],
        )
    except (requests.RequestException, pd.errors.ParserError, ValueError) as e:
        logging.exception("Could not load student data")
        st.error(f"❌ Could not load student data. {e}")
        return None

    df.columns = df.columns.str.strip().str.replace(" ", "")
    for col in df.columns:
        s = df[col]
        df[col] = s.where(s.isna(), s.astype(str).str.strip())

    df = df[df["ContractEnd"].notna() & (df["ContractEnd"].str.len() > 0)]

    def _parse_contract_end(s: str):
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return pd.to_datetime(s, format=fmt, errors="raise")
            except Exception:
                continue
        return pd.to_datetime(s, errors="coerce")

    df["ContractEnd_dt"] = df["ContractEnd"].apply(_parse_contract_end)
    df = df[df["ContractEnd_dt"].notna()]

    if "StudentCode" in df.columns:
        df["StudentCode"] = df["StudentCode"].str.lower().str.strip()
    if "Email" in df.columns:
        df["Email"] = df["Email"].str.lower().str.strip()

    df = (
        df.sort_values("ContractEnd_dt", ascending=False)
        .drop_duplicates(subset=["StudentCode"], keep="first")
        .drop(columns=["ContractEnd_dt"])
    )
    return df


def load_student_data() -> Optional[pd.DataFrame]:
    """Load student roster, or return None if unavailable."""
    return _load_student_data_cached()


__all__ = [
    "DEFAULT_PLAYLIST_LEVEL",
    "YOUTUBE_API_KEY",
    "YOUTUBE_PLAYLIST_IDS",
    "fetch_youtube_playlist_videos",
    "get_playlist_ids_for_level",
    "load_student_data",
]
