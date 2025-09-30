"""Dictionary sub-tab rendering for the vocab trainer."""
from __future__ import annotations

import difflib
import importlib
from typing import TYPE_CHECKING, Iterable, Tuple

import pandas as pd
import streamlit as st

from src.sentence_bank import SENTENCE_BANK
from src.services.vocab import VOCAB_LISTS, get_audio_url
from src.ui_components import prepare_audio_url, render_audio_player
from src.utils.toasts import refresh_with_toast

if TYPE_CHECKING:  # pragma: no cover - runtime import to avoid circular dependency
    from a1sprechen import _dict_tts_bytes_de as DictTtsFn


_DICT_TTS: object | None = None


def _get_dict_tts() -> object:
    """Return the cached ``_dict_tts_bytes_de`` helper from :mod:`a1sprechen`."""

    global _DICT_TTS
    if _DICT_TTS is None:
        app_module = importlib.import_module("a1sprechen")
        _DICT_TTS = getattr(app_module, "_dict_tts_bytes_de")
    return _DICT_TTS


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
        df = df.drop_duplicates(subset=["Level", "German"]).reset_index(drop=True)
    return df


def render_vocab_dictionary(student_level_locked: str) -> None:
    """Render the dictionary sub-tab for the selected *student_level_locked*."""

    dict_tts_bytes = _get_dict_tts()

    mapping = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}

    def _norm(value: str) -> str:
        text = (value or "").strip().lower()
        for key, repl in mapping.items():
            text = text.replace(key, repl)
        return "".join(ch for ch in text if ch.isalnum() or ch.isspace())

    available_levels = sorted(VOCAB_LISTS.keys())
    has_unknown = False
    if "nan" in available_levels:
        available_levels = [lvl for lvl in available_levels if lvl != "nan"]
        available_levels.append("Unknown level")
        has_unknown = True
    if has_unknown:
        st.info("Words without a level are listed under 'Unknown level'.")

    default_levels = (
        [student_level_locked] if student_level_locked in available_levels else []
    )
    levels_display = st.multiselect(
        "Select level(s)",
        available_levels,
        default=default_levels,
        key="dict_levels",
    )
    levels = ["nan" if lvl == "Unknown level" else lvl for lvl in levels_display]
    df_dict = build_dict_df(levels)
    for column in ["Level", "German", "English", "Pronunciation"]:
        if column not in df_dict.columns:
            df_dict[column] = ""
    df_dict["g_norm"] = df_dict["German"].astype(str).map(_norm)
    df_dict["e_norm"] = df_dict["English"].astype(str).map(_norm)
    df_dict = df_dict.sort_values(["German"]).reset_index(drop=True)

    st.markdown(
        """
        <style>
          .sticky-search { position: sticky; top: 0; z-index: 999; background: white; padding: 8px 0 10px 0; }
          input[type="text"] { font-size: 18px !important; }
          .chip { display:inline-block; padding:6px 10px; border-radius:999px; border:1px solid #e5e7eb; margin-right:6px; margin-bottom:6px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="sticky-search">', unsafe_allow_html=True)
        cols = st.columns([6, 3, 3])
        with cols[0]:
            pending_dict_q = st.session_state.pop("dict_q_pending", None)
            if pending_dict_q is not None:
                st.session_state["dict_q"] = pending_dict_q
            query = st.text_input(
                "🔎 Search (German or English)",
                key="dict_q",
                placeholder="e.g., Wochenende, bakery, spielen",
            )
        with cols[1]:
            search_in = st.selectbox("Field", ["Both", "German", "English"], 0, key="dict_field")
        with cols[2]:
            match_mode = st.selectbox(
                "Match", ["Contains", "Starts with", "Exact"], 0, key="dict_mode"
            )
        st.markdown('</div>', unsafe_allow_html=True)

    df_view = df_dict.copy()
    suggestions: list[str] = []
    top_row = None

    if query:
        normalized = _norm(query)
        if search_in in ("Both", "German"):
            g_contains = df_view["g_norm"].str.contains(normalized, na=False)
            g_starts = df_view["g_norm"].str.startswith(normalized, na=False)
            g_exact = df_view["g_norm"].eq(normalized)
        else:
            g_contains = pd.Series([False] * len(df_view))
            g_starts = pd.Series([False] * len(df_view))
            g_exact = pd.Series([False] * len(df_view))

        if search_in in ("Both", "English"):
            e_contains = df_view["e_norm"].str.contains(normalized, na=False)
            e_starts = df_view["e_norm"].str.startswith(normalized, na=False)
            e_exact = df_view["e_norm"].eq(normalized)
        else:
            e_contains = pd.Series([False] * len(df_view))
            e_starts = pd.Series([False] * len(df_view))
            e_exact = pd.Series([False] * len(df_view))

        if match_mode == "Contains":
            mask = g_contains | e_contains
        elif match_mode == "Starts with":
            mask = g_starts | e_starts
        else:
            mask = g_exact | e_exact

        if mask.any():
            exact_mask = (g_exact | e_exact) & mask
            starts_mask = (g_starts | e_starts) & mask
            df_view = df_view[mask].reset_index(drop=True)
            exact_mask = exact_mask[mask].reset_index(drop=True)
            starts_mask = starts_mask[mask].reset_index(drop=True)
            if not df_view.empty:
                if exact_mask.any():
                    top_row = df_view[exact_mask].iloc[0]
                elif starts_mask.any():
                    top_row = df_view[starts_mask].iloc[0]
                else:
                    top_row = df_view.iloc[0]
        else:
            vocab_all = df_view["German"].astype(str).unique().tolist()
            suggestions = difflib.get_close_matches(query, vocab_all, n=5, cutoff=0.72)
            if not suggestions:
                st.info("No matches found.")
            dummy = {
                "Level": student_level_locked,
                "German": query,
                "English": "",
                "Pronunciation": "",
                "g_norm": normalized,
                "e_norm": "",
            }
            df_view = pd.concat([df_view, pd.DataFrame([dummy])], ignore_index=True)
            top_row = pd.Series(dummy)
    else:
        if not df_view.empty:
            top_row = df_view.iloc[0]

    if top_row is not None and len(top_row) > 0:
        german = str(top_row["German"])
        english = str(top_row.get("English", "") or "")
        level = str(top_row.get("Level", student_level_locked))

        st.markdown(f"### {german}")
        if english:
            st.markdown(f"**Meaning:** {english}")
        pronunciation = str(top_row.get("Pronunciation", "") or "").strip()
        if pronunciation:
            st.markdown(f"**Pronunciation:** {pronunciation}")

        example_sentence = ""
        for item in SENTENCE_BANK.get(level, []):
            tokens = [str(tok).strip().lower() for tok in item.get("tokens", [])]
            if german.lower() in tokens:
                example_sentence = (
                    item.get("target_de") or " ".join(item.get("tokens", []))
                )
                break
        if example_sentence:
            st.markdown(example_sentence)

        sheet_audio = get_audio_url(level, german)
        sheet_audio = prepare_audio_url(sheet_audio) if sheet_audio else None
        if sheet_audio:
            render_audio_player(sheet_audio, verified=True)
            st.markdown(f"[⬇️ Download / Open MP3]({sheet_audio})")
        else:
            audio_bytes = dict_tts_bytes(german)
            if audio_bytes:
                render_audio_player(audio_bytes)
                st.download_button(
                    "⬇️ Download MP3",
                    data=audio_bytes,
                    file_name=f"{german}.mp3",
                    mime="audio/mpeg",
                    key=f"dl_{german}_{level}",
                )
            else:
                st.caption("Audio not available yet.")

    if query and suggestions:
        st.markdown("**Did you mean:**")
        button_cols = st.columns(min(5, len(suggestions)))
        for idx, suggestion in enumerate(suggestions[:5]):
            with button_cols[idx]:
                if st.button(suggestion, key=f"sugg_{idx}"):
                    st.session_state["dict_q_pending"] = suggestion
                    refresh_with_toast()

    levels_label = ", ".join(levels) if levels else "none"
    with st.expander(
        f"Browse all words for levels: {levels_label}", expanded=False
    ):
        df_show = df_view[["German", "English"]].copy()
        st.dataframe(df_show, width="stretch", height=420)
