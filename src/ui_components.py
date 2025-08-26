"""Small reusable UI components for Streamlit."""

from __future__ import annotations

import pandas as pd
import streamlit as st

try:  # pragma: no cover - dependency might be missing in some environments
    from rapidfuzz import process
except Exception:  # pragma: no cover
    process = None

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
        st.caption(
            "For longer phrases, try [DeepL](https://www.deepl.com/translator) or [Google Translate](https://translate.google.com)."
        )

    query = st.text_input("🔎 Search vocabulary", key=f"vocab-{key}")
    if not query:
        return

    mask = df.apply(
        lambda row: row.astype(str).str.contains(query, case=False, na=False).any(),
        axis=1,
    )
    search_col = next(
        (col for col in ["German", "Word"] if col in df.columns), df.columns[0]
    )
    translation_col = next(
        (
            col
            for col in ["English", "Translation", "Meaning"]
            if col in df.columns and col != search_col
        ),
        df.columns[1] if len(df.columns) > 1 else search_col,
    )

    columns = [search_col, translation_col]
    for col in ["Audio", "Audio Link"]:
        if col in df.columns and col not in columns:
            columns.append(col)

    results = df.loc[mask, columns]

    if results.empty and process is not None:
        choices = df[search_col].dropna().astype(str).tolist()
        fuzzy_matches = process.extract(query, choices, limit=5)
        matched_values = [match[0] for match in fuzzy_matches]
        results = df[df[search_col].isin(matched_values)][columns]
        
    if results.empty:
        st.write("No matches found.")
    else:
        for _, row in results.iterrows():
            word = row[search_col]
            meaning = row[translation_col]
            audio_url = row.get("Audio")
            if not audio_url or pd.isna(audio_url):
                audio_url = row.get("Audio Link")
            if not audio_url or pd.isna(audio_url):
                audio_url = None

            line = f"- **{word}** – {meaning}"
            if audio_url:
                line += f" [▶️]({audio_url}) [⬇️]({audio_url})"
            st.markdown(line)
            if audio_url:
                try:  # pragma: no cover - best effort on mobile browsers
                    st.audio(audio_url)
                except Exception:
                    pass
