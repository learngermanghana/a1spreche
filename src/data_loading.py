"""Data loading helpers for a1sprechen.

Exports :func:`load_student_data` for retrieving the student roster.
"""

from __future__ import annotations

import io
import logging
import time
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from .youtube import (  # noqa: F401
    DEFAULT_PLAYLIST_LEVEL,
    YOUTUBE_API_KEY,
    YOUTUBE_PLAYLIST_IDS,
    get_playlist_ids_for_level,
    fetch_youtube_playlist_videos,
)

# ------------------------------------------------------------------------------
# Student roster loading
# ------------------------------------------------------------------------------

# You can override this with st.secrets["ROSTER_CSV_URL"]
GOOGLE_SHEET_CSV = (
    "https://docs.google.com/spreadsheets/d/12NXf5FeVHr7JJT47mRHh7Jp-TC1yhPS7ZG6nzZVTt1U/"
    "gviz/tq?tqx=out:csv&sheet=Sheet1"
)

_REQUEST_HEADERS = {
    # Helps avoid cached intermediaries
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    # Some endpoints behave differently for non-browser UAs
    "User-Agent": "Mozilla/5.0 (compatible; a1sprechen/1.0; +streamlit)",
}

class _NoUsableData(RuntimeError):
    """Signal that the fetch succeeded but produced no usable rows.
    We raise (instead of returning None) so cache_data does NOT cache this state.
    """

def _with_cache_buster(url: str) -> str:
    # Changes once per minute to avoid CDN/Sheets staleness on first render
    cb = int(time.time() // 60)
    sep = "&" if ("?" in url) else "?"
    return f"{url}{sep}cb={cb}"


@st.cache_data(ttl=300, show_spinner=False)
def _load_student_data_cached(csv_url: str) -> pd.DataFrame:
    """Fetch and parse the student roster from the given CSV URL.

    Raises
    ------
    requests.RequestException | pd.errors.ParserError | ValueError | _NoUsableData
    """
    try:
        resp = requests.get(csv_url, timeout=12, headers=_REQUEST_HEADERS)
        resp.raise_for_status()
        txt = resp.text
        # Guard against HTML interstitials (private sheet / auth / rate limit)
        if "<html" in txt[:512].lower():
            raise ValueError("Expected CSV, got HTML (check sheet privacy/sharing).")
        df = pd.read_csv(
            io.StringIO(txt),
            dtype=str,
            keep_default_na=True,
            na_values=["", " ", "nan", "NaN", "None"],
        )
    except (requests.RequestException, pd.errors.ParserError, ValueError) as e:
        logging.exception("Could not load student data")
        st.error(f"❌ Could not load student data. {e}")
        raise

    # Basic normalization
    df.columns = df.columns.str.strip().str.replace(" ", "", regex=False)
    if df.empty:
        st.info("No rows found in the roster sheet.")
        raise _NoUsableData("Empty roster")

    # --- Column aliasing -------------------------------------------------------
    # Make 'ClassName' robust to different labels
    lower_cols = {c.lower(): c for c in df.columns}
    classname_aliases = [
        "classname", "class", "classroom", "class_name",
        "group", "groupname", "group_name",
        "course", "coursename", "course_name",
    ]
    if "classname" in lower_cols and lower_cols["classname"] != "ClassName":
        df.rename(columns={lower_cols["classname"]: "ClassName"}, inplace=True)
    elif "classname" not in lower_cols:
        for alias in classname_aliases:
            if alias in lower_cols:
                df.rename(columns={lower_cols[alias]: "ClassName"}, inplace=True)
                break

    # Contract end aliases (Sheet can vary)
    contract_aliases = [
        "contractend", "contract_end", "contractenddate", "contract_end_date",
        "enddate", "end_date", "end", "expires", "expiry", "expirydate", "expiry_date",
    ]
    if "ContractEnd" not in df.columns:
        lc = {c.lower(): c for c in df.columns}
        for alias in contract_aliases:
            if alias in lc:
                df.rename(columns={lc[alias]: "ContractEnd"}, inplace=True)
                break

    if "ClassName" not in df.columns:
        supported = ", ".join(["ClassName"] + classname_aliases)
        raise ValueError(
            "Student roster is missing a 'ClassName' column. "
            f"Supported column names: {supported}"
        )

    if "ContractEnd" not in df.columns:
        logging.warning("Student roster missing 'ContractEnd' column")
        st.warning("The student roster is missing a 'ContractEnd' (or equivalent) column.")
        raise _NoUsableData("Missing ContractEnd")

    # Strip whitespace in all string columns
    for col in df.columns:
        s = df[col]
        df[col] = s.where(s.isna(), s.astype(str).str.strip())

    # Keep rows with a non-empty ContractEnd
    df = df[df["ContractEnd"].notna() & (df["ContractEnd"].str.len() > 0)]

    # Parse ContractEnd with several common formats, then coerce
    def _parse_contract_end(s: str):
        for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return pd.to_datetime(s, format=fmt, errors="raise")
            except Exception:
                continue
        return pd.to_datetime(s, errors="coerce")

    df["ContractEnd_dt"] = df["ContractEnd"].apply(_parse_contract_end)
    df = df[df["ContractEnd_dt"].notna()]

    # Normalize helpful columns
    if "StudentCode" in df.columns:
        df["StudentCode"] = df["StudentCode"].str.lower().str.strip()
    if "Email" in df.columns:
        df["Email"] = df["Email"].str.lower().str.strip()

    # Sort/unique
    df = df.sort_values("ContractEnd_dt", ascending=False)
    if "StudentCode" in df.columns:
        df = df.drop_duplicates(subset=["StudentCode"], keep="first")
    df = df.drop(columns=["ContractEnd_dt"], errors="ignore")

    if df.empty:
        st.info("No active students found with a valid 'ContractEnd'.")
        raise _NoUsableData("No active students")

    return df


def load_student_data(force_refresh: bool = False) -> Optional[pd.DataFrame]:
    """Load student roster.

    Returns ``None`` if the roster contains no usable rows. Any errors during
    loading (network/parse/validation) are propagated to the caller.
    """
    # Allow overriding the URL via secrets
    base = st.secrets.get("ROSTER_CSV_URL", GOOGLE_SHEET_CSV)
    url = _with_cache_buster(base)

    if force_refresh:
        try:
            _load_student_data_cached.clear()
        except Exception:
            logging.exception("Unable to clear cached student roster")

    try:
        return _load_student_data_cached(url)
    except _NoUsableData:
        # Present as "no data" to the caller but DO NOT cache this state
        return None


__all__ = ["load_student_data"]
