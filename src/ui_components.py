"""Small reusable UI components for Streamlit."""

from __future__ import annotations

import pandas as pd
import streamlit as st

# Google Sheet ID for vocabulary lookup
VOCAB_SHEET_ID = "1I1yAnqzSh3DPjwWRh9cdRSfzNSPsi7o4r5Taj9Y36NU"


@st.cache_data(show_spinner=False)
def _load_vocab_sheet(sheet_id: str = VOCAB_SHEET_ID) -> pd.DataFrame | None:
    """Download the vocabulary sheet as a DataFrame.

    Returns ``None`` if the sheet cannot be loaded.
    """

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        return pd.read_csv(url)
    except Exception:  # pragma: no cover - network or parsing issues
        return None


def render_assignment_reminder() -> None:
    """Show a yellow assignment reminder box."""

    st.markdown(
        '''
        <div style="
            box-sizing: border-box;
            width: 100%;
            max-width: 600px;
            padding: 16px;
            background: #ffc107;
            color: #000;
            border-left: 6px solid #e0a800;
            margin: 16px auto;
            border-radius: 8px;
            font-size: 1.1rem;
            line-height: 1.4;
            text-align: center;
            overflow-wrap: break-word;
            word-wrap: break-word;
        ">
            ⬆️ <strong>Your Assignment:</strong><br>
            Complete the exercises in your <em>workbook</em> for this chapter.
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_link(label: str, url: str) -> None:
    """Render a bullet link."""

    st.markdown(f"- [{label}]({url})")


def render_vocab_lookup(key: str) -> None:
    """Render a small vocabulary lookup widget.

    Parameters
    ----------
    key:
        Unique key so Streamlit state doesn't clash across lessons.
    """

    df = _load_vocab_sheet()
    if df is None:
        st.info("Vocabulary lookup currently unavailable.")
        return

    query = st.text_input("🔎 Search vocabulary", key=f"vocab-{key}")
    if not query:
        return

    mask = df.apply(
        lambda row: row.astype(str).str.contains(query, case=False, na=False).any(),
        axis=1,
    )
    results = df[mask]
    if results.empty:
        st.write("No matches found.")
    else:
        st.dataframe(results, use_container_width=True, height=200)
