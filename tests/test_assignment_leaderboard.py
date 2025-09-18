import pandas as pd

from src.assignment_ui import select_best_assignment_attempts


def test_leaderboard_ignores_lower_duplicate_scores():
    df = pd.DataFrame(
        {
            "studentcode": ["s1", "s1", "s1", "s2", "s2"],
            "assignment": ["A", "A", "B", "A", "A"],
            "score": ["40", "85", "90", "50", "65"],
            "level": ["A1", "A1", "A1", "A1", "A1"],
            "name": ["Student 1", "Student 1", "Student 1", "Student 2", "Student 2"],
        }
    )

    deduped = select_best_assignment_attempts(df)
    deduped["score"] = pd.to_numeric(deduped["score"], errors="coerce")

    leaderboard = (
        deduped[deduped["level"] == "A1"]
        .groupby(["studentcode", "name"], as_index=False)
        .agg(total_score=("score", "sum"), completed=("assignment", "nunique"))
        .set_index("studentcode")
    )

    assert len(deduped) == 3  # Only one row per student/assignment pair
    assert leaderboard.loc["s1", "total_score"] == 175.0
    assert leaderboard.loc["s1", "completed"] == 2
    assert leaderboard.loc["s2", "total_score"] == 65.0
    assert leaderboard.loc["s2", "completed"] == 1
