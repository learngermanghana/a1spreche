import ast
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd


def _load_assignment_date_helper():
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    assign_names = {
        "CONTRACT_DATE_FORMATS",
        "_ASSIGNMENT_DATE_COLUMNS",
        "_ASSIGNMENT_DATE_REGEX_PATTERNS",
    }
    func_names = {"_parse_contract_date_value", "_normalize_assignment_submission_dates"}

    nodes: list[Any] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id in assign_names for target in node.targets):
                nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in func_names:
            nodes.append(node)

    module = ast.Module(body=nodes, type_ignores=[])
    glb = {
        "Any": Any,
        "Iterable": Iterable,
        "Optional": Optional,
        "UTC": UTC,
        "datetime": datetime,
        "date": date,
        "pd": pd,
        "re": re,
    }
    exec(compile(module, "a1sprechen.py", "exec"), glb)
    return glb["_normalize_assignment_submission_dates"]


def test_assignment_streak_handles_mixed_date_formats():
    normalize_dates = _load_assignment_date_helper()
    df = pd.DataFrame(
        {
            "studentcode": ["abc123"] * 5,
            "submitted_on": [
                "2025-09-23",
                "Submitted: 2025-09-23",
                "2025-09-22",
                "23/09/2025",
                "Submitted: 2025-09-21",
            ],
        }
    )

    df["date"] = normalize_dates(df)

    assert list(df["date"].notna()) == [True] * len(df)
    assert df.loc[1, "date"] == date(2025, 9, 23)
    assert df.loc[3, "date"] == date(2025, 9, 23)
    assert df.loc[4, "date"] == date(2025, 9, 21)

    mask = df["studentcode"].str.lower().str.strip() == "abc123"
    dates = sorted(df[mask]["date"].dropna().unique(), reverse=True)

    assert dates == [date(2025, 9, 23), date(2025, 9, 22), date(2025, 9, 21)]

    streak = 1 if dates else 0
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break

    assert streak == 3
