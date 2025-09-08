"""Utilities for loading vocabulary lists and audio URLs."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd
import streamlit as st

SHEET_ID = "1I1yAnqzSh3DPjwWRh9cdRSfzNSPsi7o4r5Taj9Y36NU"
SHEET_GID = 0  # <-- change this if your Vocab tab uses another gid


@st.cache_data
def load_vocab_lists() -> Tuple[Dict[str, list], Dict[Tuple[str, str], Dict[str, str]]]:
    """Load vocabulary and audio URLs from the configured Google Sheet."""
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:  # pragma: no cover - network errors
        st.error(f"Could not fetch vocab CSV: {e}")
        return {}, {}

    df.columns = df.columns.str.strip()

    required = ["German", "English"]
    missing_required = [c for c in required if c not in df.columns]
    if missing_required:
        st.error(f"Missing column(s) in your vocab sheet: {missing_required}")
        return {}, {}

    if "Level" not in df.columns:
        st.warning("Missing 'Level' column in your vocab sheet. Defaulting to 'A1'.")
        df["Level"] = "A1"

    df["Level"] = df["Level"].astype(str).str.strip()
    df["German"] = df["German"].astype(str).str.strip()
    df["English"] = df["English"].astype(str).str.strip()
    has_pron = "Pronunciation" in df.columns
    if not has_pron:
        df["Pronunciation"] = ""
    df["Pronunciation"] = df["Pronunciation"].astype(str).str.strip()
    df = df.dropna(subset=["Level", "German"])

    def pick(*names):
        for n in names:
            if n in df.columns:
                return n
        return None

    normal_col = pick("Audio (normal)", "Audio normal", "Audio_Normal", "Audio")
    slow_col = pick("Audio (slow)", "Audio slow", "Audio_Slow")

    if has_pron:
        vocab_lists = {
            lvl: list(zip(grp["German"], grp["English"], grp["Pronunciation"]))
            for lvl, grp in df.groupby("Level")
        }
    else:
        vocab_lists = {
            lvl: list(zip(grp["German"], grp["English"])) for lvl, grp in df.groupby("Level")
        }
    audio_urls: Dict[Tuple[str, str], Dict[str, str]] = {}
    for _, r in df.iterrows():
        key = (r["Level"], r["German"])
        audio_urls[key] = {
            "normal": str(r.get(normal_col, "")).strip() if normal_col else "",
            "slow": str(r.get(slow_col, "")).strip() if slow_col else "",
        }
    return vocab_lists, audio_urls


VOCAB_LISTS, AUDIO_URLS = load_vocab_lists()


def refresh_vocab_from_sheet() -> None:
    load_vocab_lists.clear()
    global VOCAB_LISTS, AUDIO_URLS
    VOCAB_LISTS, AUDIO_URLS = load_vocab_lists()


def get_audio_url(level: str, german_word: str) -> str:
    """Prefer slow audio for A1, otherwise normal, falling back appropriately."""
    urls = AUDIO_URLS.get((str(level).upper(), str(german_word).strip()), {})
    lvl = str(level).upper()
    return (urls.get("slow") if (lvl == "A1" and urls.get("slow")) else urls.get("normal")) or urls.get("slow") or ""


__all__ = [
    "SHEET_ID",
    "SHEET_GID",
    "VOCAB_LISTS",
    "AUDIO_URLS",
    "load_vocab_lists",
    "refresh_vocab_from_sheet",
    "get_audio_url",
]
