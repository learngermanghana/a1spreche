"""Streamlit page to display the assignment leaderboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.assignment_ui import load_assignment_scores


# ---------------------------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------------------------

def _prepare_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """Return leaderboard DataFrame aggregated by level and student."""
    if df.empty:
        return pd.DataFrame(columns=["level", "studentcode", "name", "total_score", "completed", "rank"])

    # Normalise columns
    df = df.copy()
    df["level"] = df["level"].astype(str).str.upper().str.strip()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")

    # Aggregate totals per student
    grouped = (
        df.groupby(["level", "studentcode", "name"], as_index=False)
        .agg(total_score=("score", "sum"), completed=("assignment", "nunique"))
    )

    # Keep students with enough completed assignments
    grouped = grouped[grouped["completed"] >= 3]
    if grouped.empty:
        return grouped

    # Sort and rank within each level
    grouped = grouped.sort_values(["level", "total_score", "completed"], ascending=[True, False, False])
    grouped["rank"] = grouped.groupby("level").cumcount() + 1
    return grouped


# ---------------------------------------------------------------------------
# Streamlit page
# ---------------------------------------------------------------------------

def render_page() -> None:
    """Render the leaderboard for the current user's level."""
    scores_df = load_assignment_scores()
    leaderboard_df = _prepare_leaderboard(scores_df)

    # Determine the current user's level
    student_row = st.session_state.get("student_row") or {}
    current_level = (student_row.get("Level") or "").upper().strip()

    if current_level:
        leaderboard_df = leaderboard_df[leaderboard_df["level"] == current_level]

    st.dataframe(leaderboard_df, hide_index=True)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    render_page()
