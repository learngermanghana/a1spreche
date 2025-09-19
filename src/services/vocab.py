"""Utilities for loading vocabulary lists and audio URLs."""

from __future__ import annotations

import os
from typing import Dict, Tuple, Union

import pandas as pd
import streamlit as st

DEFAULT_SHEET_ID = "1I1yAnqzSh3DPjwWRh9cdRSfzNSPsi7o4r5Taj9Y36NU"
DEFAULT_SHEET_GID = 0  # <-- change this if your Vocab tab uses another gid


def _lookup_secret(*keys: str) -> Union[str, int, None]:
    """Return the first matching value from ``st.secrets`` for ``keys``."""

    secrets = getattr(st, "secrets", None)
    if not secrets:  # pragma: no cover - streamlit always provides secrets
        return None
    for key in keys:
        try:
            if key in secrets:  # type: ignore[operator]
                return secrets[key]
        except TypeError:  # pragma: no cover - defensive for custom secrets
            value = getattr(secrets, key, None)
            if value is not None:
                return value
    return None


def _coerce_gid(raw_value: Union[str, int, None]) -> int:
    """Convert a user-provided gid to an ``int`` or fall back to the default."""

    if raw_value in (None, ""):
        return DEFAULT_SHEET_GID
    if isinstance(raw_value, int):
        return raw_value
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        return DEFAULT_SHEET_GID


def get_vocab_sheet_config() -> Tuple[str, int]:
    """Resolve the configured sheet id and gid from env vars or secrets."""

    sheet_id = os.getenv("VOCAB_SHEET_ID") or _lookup_secret(
        "VOCAB_SHEET_ID", "vocab_sheet_id"
    )
    if not sheet_id:
        sheet_id = DEFAULT_SHEET_ID
    sheet_id = str(sheet_id)

    raw_gid = os.getenv("VOCAB_SHEET_GID")
    if raw_gid in (None, ""):
        raw_gid = _lookup_secret("VOCAB_SHEET_GID", "vocab_sheet_gid")
    sheet_gid = _coerce_gid(raw_gid)

    return sheet_id, sheet_gid


SHEET_ID, SHEET_GID = get_vocab_sheet_config()


def _build_vocab_csv_url() -> str:
    """Construct the CSV export URL for the configured sheet."""

    sheet_id, sheet_gid = get_vocab_sheet_config()
    global SHEET_ID, SHEET_GID
    SHEET_ID, SHEET_GID = sheet_id, sheet_gid
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/"
        f"export?format=csv&gid={sheet_gid}"
    )


@st.cache_data
def load_vocab_lists() -> Tuple[Dict[str, list], Dict[Tuple[str, str], Dict[str, str]]]:
    """Load vocabulary and audio URLs from the configured Google Sheet."""
    csv_url = _build_vocab_csv_url()
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

    # Remove rows with missing Level or German before converting to strings.
    df = df.dropna(subset=["Level", "German"])

    df["Level"] = df["Level"].astype(str).str.strip()
    df["German"] = df["German"].astype(str).str.strip()
    df["English"] = df["English"].astype(str).str.strip()
    has_pron = "Pronunciation" in df.columns
    if not has_pron:
        df["Pronunciation"] = ""
    df["Pronunciation"] = df["Pronunciation"].astype(str).str.strip()

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
    "get_vocab_sheet_config",
    "load_vocab_lists",
    "refresh_vocab_from_sheet",
    "get_audio_url",
]
