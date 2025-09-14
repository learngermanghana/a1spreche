"""Data loading helpers for a1sprechen.

Exports :func:`load_student_data` for retrieving the student roster.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from .youtube import (
    DEFAULT_PLAYLIST_LEVEL,
    YOUTUBE_API_KEY,
    YOUTUBE_PLAYLIST_IDS,
    get_playlist_ids_for_level,
    fetch_youtube_playlist_videos,
)  # noqa: F401


# ------------------------------------------------------------------------------
# Student roster loading
# ------------------------------------------------------------------------------

GOOGLE_SHEET_CSV = (
    "https://docs.google.com/spreadsheets/d/12NXf5FeVHr7JJT47mRHh7Jp-TC1yhPS7ZG6nzZVTt1U/"
    "gviz/tq?tqx=out:csv&sheet=Sheet1"
)


@st.cache_data(ttl=300)
def _load_student_data_cached() -> Optional[pd.DataFrame]:
    """Fetch the student roster from the Google Sheet.

    Returns
    -------
    Optional[pd.DataFrame]
        Parsed student roster if rows are available, ``None`` if the sheet
        contains no usable data.

    Raises
    ------
    requests.RequestException | pd.errors.ParserError | ValueError
        If the request fails or the response cannot be parsed.  These
        exceptions are logged, displayed via Streamlit, and re-raised so
        callers can distinguish data errors from missing data.
    """

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
        raise

    df.columns = df.columns.str.strip().str.replace(" ", "")

    # Normalize common variants of the class name column so downstream
    # components can reliably access ``ClassName`` regardless of how the
    # roster labels it.  Some spreadsheets use ``Class`` or a lowercase
    # ``classname``; unify these to ``ClassName``.
    lower_cols = {c.lower(): c for c in df.columns}
    if "classname" in lower_cols and lower_cols["classname"] != "ClassName":
        df.rename(columns={lower_cols["classname"]: "ClassName"}, inplace=True)
    elif "class" in lower_cols and "classname" not in lower_cols:
        df.rename(columns={lower_cols["class"]: "ClassName"}, inplace=True)
    elif "classroom" in lower_cols and "classname" not in lower_cols:
        df.rename(columns={lower_cols["classroom"]: "ClassName"}, inplace=True)

    for col in df.columns:
        s = df[col]
        df[col] = s.where(s.isna(), s.astype(str).str.strip())
    if "ContractEnd" not in df.columns:
        logging.warning("Student roster missing 'ContractEnd' column")
        st.warning("The student roster is missing a 'ContractEnd' column.")
        return None

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
    if df.empty:
        return None
    return df


def load_student_data() -> Optional[pd.DataFrame]:
    """Load student roster.

    Returns ``None`` if the roster contains no usable rows. Any errors during
    loading are propagated to the caller.
    """
    return _load_student_data_cached()


# Only ``load_student_data`` is part of the public API now that the
# YouTube helpers live elsewhere.
__all__ = ["load_student_data"]
