import ast
import math
import re
import textwrap
import types
from pathlib import Path
from datetime import datetime, UTC
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import pytest

from src.assignment_ui import summarize_assignment_attempts, PASS_MARK


def _load_status_helper():
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    class Finder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.positions: Dict[str, tuple[int, int]] = {}

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pragma: no cover - AST traversal helper
            self.positions[node.name] = (node.lineno, node.end_lineno)
            self.generic_visit(node)

    finder = Finder()
    finder.visit(tree)

    start = finder.positions["_extract_assignment_numbers_for_resubmit"][0] - 1
    end = finder.positions["_build_coursebook_status_payload"][1]
    snippet = textwrap.dedent("\n".join(source.splitlines()[start:end]))

    mod = types.ModuleType("coursebook_status_helper")
    mod.pd = pd
    mod.math = math
    mod.re = re
    mod.datetime = datetime
    mod.UTC = UTC
    mod.PASS_MARK = PASS_MARK
    mod._ASSIGNMENT_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")
    mod.MIN_RESUBMIT_WORD_COUNT = 20
    mod.Iterable = Iterable
    mod.List = List
    mod.Dict = Dict
    mod.Optional = Optional
    mod.Any = Any

    exec(snippet, mod.__dict__)
    return mod._build_coursebook_status_payload


@pytest.fixture(scope="module")
def status_helper():
    return _load_status_helper()


def _make_summary(score_value):
    data = {
        "assignment": ["Day 1 – 1.0"],
        "score": [score_value],
        "studentcode": ["S1"],
        "level": ["A1"],
        "date": ["2024-01-01"],
    }
    df = pd.DataFrame(data)
    return summarize_assignment_attempts(df)


@pytest.mark.parametrize(
    "needs_resubmit,score_value,expected_label",
    [
        (True, 50, "Resubmit needed"),
        (False, 85, "Passed"),
        (False, None, "In review"),
    ],
)
def test_coursebook_status_helper_labels(status_helper, needs_resubmit, score_value, expected_label):
    summary_df = _make_summary(score_value)
    latest = {
        "answer": "Hallo",
        "updated_at": datetime(2024, 1, 2, 15, 30, tzinfo=UTC),
    }

    payload = status_helper(
        latest_submission=latest,
        needs_resubmit=needs_resubmit,
        attempts_summary=summary_df,
        assignment_identifiers=[1.0],
    )

    assert payload["label"] == expected_label

    lines = " ".join(payload.get("meta_lines", []))
    if score_value is not None and score_value >= PASS_MARK:
        assert "85" in lines
    if expected_label == "In review":
        assert any("Last submitted" in line for line in payload.get("meta_lines", []))

