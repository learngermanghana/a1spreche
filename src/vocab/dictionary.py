"""Dictionary sub-tab rendering for the vocab trainer."""
from __future__ import annotations

from typing import Iterable, Tuple

import pandas as pd
import streamlit as st

from src.sentence_bank import SENTENCE_BANK
from src.services.vocab import VOCAB_LISTS


@st.cache_data
def build_dict_df(levels: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    sentence_map: dict[Tuple[str, str], str] = {}

    for lvl in levels:
        for item in SENTENCE_BANK.get(lvl, []):
            sentence = item.get("target_de", "")
            for token in item.get("tokens", []):
                tok = str(token).strip()
                if not tok or tok in [",", ".", "!", "?", ":", ";"]:
                    continue
                sentence_map.setdefault((lvl, tok), sentence)

    for lvl in levels:
        for entry in VOCAB_LISTS.get(lvl, []):
            de = entry[0]
            en = entry[1]
            pron = entry[2] if len(entry) > 2 else ""
            sent = sentence_map.get((lvl, de), "")
            rows.append(
                {
                    "Level": lvl,
                    "German": de,
                    "English": en,
                    "Pronunciation": pron,
                    "Sentence": sent,
                }
            )

    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(
            columns=["Level", "German", "English", "Pronunciation", "Sentence"]
        )

    extra = []
    for (lvl, tok), sent in sentence_map.items():
        if not ((df["German"] == tok) & (df["Level"] == lvl)).any():
            extra.append(
                {
                    "Level": lvl,
                    "German": tok,
                    "English": "",
                    "Pronunciation": "",
                    "Sentence": sent,
                }
            )
    if extra:
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)

    if not df.empty:
        # Only remove exact duplicate rows.  Previously we dropped everything that
        # shared the same ``Level`` and ``German`` value which meant multiple
        # legitimate entries (for example when a word appears twice with different
        # English translations) were collapsed into one.  That made the counts in
        # the UI lower than the actual number of rows in the Google Sheet.  By
        # considering every column we keep intentional duplicates while still
        # deduplicating rows that are truly identical.
        df = df.drop_duplicates().reset_index(drop=True)
    return df


def render_vocab_dictionary(student_level_locked: str) -> None:
    """Render the All Vocabs sub-tab for the selected *student_level_locked*."""

    st.markdown("### 📖 All Vocabs")
    st.caption(
        "Browse the vocabulary that is available in the Vocab Trainer. "
        "Use the practice sub-tab for exercises—this page is for reference only."
    )

    available_levels = sorted(VOCAB_LISTS.keys())
    if not available_levels:
        st.info("No vocabulary lists are available yet.")
        return

    has_unknown = False
    if "nan" in available_levels:
        available_levels = [lvl for lvl in available_levels if lvl != "nan"]
        available_levels.append("Unknown level")
        has_unknown = True
    if has_unknown:
        st.info("Words without a level are listed under 'Unknown level'.")

    default_levels = (
        [student_level_locked]
        if student_level_locked in available_levels
        else available_levels
    )

    levels_display = st.multiselect(
        "Select level(s) to display",
        available_levels,
        default=default_levels,
        key="dict_levels",
    )

    if not levels_display:
        st.info("Choose at least one level to show its vocabulary.")
        return

    levels = ["nan" if lvl == "Unknown level" else lvl for lvl in levels_display]
    df_dict = build_dict_df(levels)

    if df_dict.empty:
        st.warning("No vocabulary entries found for the selected level(s) yet.")
        return

    for column in ["Level", "German", "English", "Pronunciation", "Sentence"]:
        if column not in df_dict.columns:
            df_dict[column] = ""

    df_dict = df_dict.sort_values(["Level", "German"]).reset_index(drop=True)

    total_words = len(df_dict.index)
    levels_label = ", ".join(levels_display)
    st.markdown(
        f"Showing **{total_words}** words across level(s): **{levels_label}**."
    )

    display_columns = ["Level", "German", "English"]
    if df_dict["Pronunciation"].str.strip().any():
        display_columns.append("Pronunciation")
    if df_dict["Sentence"].str.strip().any():
        display_columns.append("Sentence")

    st.dataframe(
        df_dict[display_columns],
        use_container_width=True,
        hide_index=True,
    )
