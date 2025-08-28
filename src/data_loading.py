"""Data loading helpers for a1sprechen.

Exports :func:`load_student_data` for retrieving the student roster.
"""

from __future__ import annotations

import io
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


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


# Only ``load_student_data`` is part of the public API now that the
# YouTube helpers live elsewhere.
__all__ = ["load_student_data"]
