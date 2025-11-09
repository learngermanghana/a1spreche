"""Helpers for surfacing quick language support suggestions for lessons."""

from __future__ import annotations
import re
from typing import Iterable, Mapping, Sequence

import pandas as pd

_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "you",
    "your",
    "about",
    "will",
    "have",
    "this",
    "that",
    "sich",
    "und",
    "der",
    "die",
    "das",
    "ein",
    "eine",
    "auf",
    "sind",
    "von",
    "den",
    "dem",
    "ist",
    "soll",
    "are",
    "into",
    "learn",
    "lesson",
    "chapter",
    "goal",
    "topic",
    "grammar",
    "focus",
}


def _iter_text_sources(info: Mapping[str, object]) -> Iterable[str]:
    """Yield string-ish metadata from ``info`` including nested section bits."""

    simple_keys = ("goal", "topic", "chapter", "grammar_topic", "instruction")
    for key in simple_keys:
        value = info.get(key)
        if isinstance(value, str):
            yield value

    def _yield_from_mapping(mapping: Mapping[str, object]) -> Iterable[str]:
        for val in mapping.values():
            if isinstance(val, str):
                yield val

    for value in info.values():
        if isinstance(value, Mapping):
            yield from _yield_from_mapping(value)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                if isinstance(item, Mapping):
                    yield from _yield_from_mapping(item)


def _normalise_keywords(chunks: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for chunk in chunks:
        for raw in re.findall(r"[A-Za-zÄÖÜäöüß]+", chunk.lower()):
            if len(raw) < 3 or raw in _STOPWORDS:
                continue
            tokens.add(raw)
    return tokens


def gather_language_support(
    info: Mapping[str, object] | None,
    level_key: str,
    vocab_df: pd.DataFrame | None,
    vocab_lists: Mapping[str, Sequence[Sequence[str]]],
    *,
    limit: int = 3,
) -> list[dict[str, str]]:
    """Return up to ``limit`` vocab suggestions relevant to ``info``.

    ``vocab_df`` should contain ``level``, ``german``, ``english`` and optional
    ``example`` columns. When it is empty or no rows match the lesson keywords,
    the function falls back to ``vocab_lists`` (which mirrors ``VOCAB_LISTS``).
    """

    if limit <= 0:
        return []

    info = info or {}
    level = (level_key or "").upper()
    keywords = _normalise_keywords(_iter_text_sources(info))

    suggestions: list[dict[str, str]] = []

    if isinstance(vocab_df, pd.DataFrame) and not vocab_df.empty:
        subset = vocab_df.copy()
        if "level" in subset.columns:
            subset["level"] = subset["level"].astype(str).str.upper()
            subset = subset[subset["level"] == level]
        else:
            subset = subset.iloc[0:0]

        scored_rows: list[tuple[int, int, dict[str, str]]] = []
        for idx, row in subset.reset_index(drop=True).iterrows():
            german = str(row.get("german", "")).strip()
            english = str(row.get("english", "")).strip()
            example = str(row.get("example", "")).strip()
            if not german and not english:
                continue
            haystack = " ".join(filter(None, [german.lower(), english.lower(), example.lower()]))
            if keywords:
                score = sum(1 for kw in keywords if kw and kw in haystack)
                if not score:
                    continue
            else:
                score = 0
            scored_rows.append((score, idx, {"german": german, "english": english, "example": example}))

        if scored_rows:
            scored_rows.sort(key=lambda item: (-item[0], item[1]))
            suggestions = [entry for _, _, entry in scored_rows[:limit]]

    if not suggestions:
        fallback = vocab_lists.get(level) or vocab_lists.get(level_key) or []
        for entry in fallback:
            if not entry:
                continue
            german = str(entry[0]).strip()
            english = str(entry[1]).strip() if len(entry) > 1 else ""
            example = str(entry[2]).strip() if len(entry) > 2 else ""
            if not german and not english:
                continue
            suggestions.append({"german": german, "english": english, "example": example})
            if len(suggestions) >= limit:
                break

    return suggestions[:limit]


__all__ = ["gather_language_support"]
