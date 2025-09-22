import ast
import math
import re
import textwrap
import types
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pytest


def _load_submit_status_helper():
    src_path = Path("a1sprechen.py")
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    class Finder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.positions: Dict[str, tuple[int, int]] = {}

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pragma: no cover - AST helper
            self.positions[node.name] = (node.lineno, node.end_lineno)
            self.generic_visit(node)

    finder = Finder()
    finder.visit(tree)

    start, end = finder.positions["_derive_coursebook_submit_status"]
    snippet = textwrap.dedent("\n".join(source.splitlines()[start - 1 : end]))

    module = types.ModuleType("submit_status_helper")
    module.math = math
    module.re = re
    module.Any = Any
    module.Dict = Dict
    module.Optional = Optional
    module.Callable = Callable

    exec(snippet, module.__dict__)
    return module


@pytest.fixture()
def submit_status_helper():
    module = _load_submit_status_helper()
    helper = module._derive_coursebook_submit_status
    return helper, module


def test_submit_status_in_review(submit_status_helper, monkeypatch):
    helper, module = submit_status_helper
    monkeypatch.setattr(module, "fetch_latest_score", lambda *_: None, raising=False)

    state = helper(
        locked=True,
        needs_resubmit=None,
        latest_submission={"answer": "Hallo"},
        student_code="S1",
        lesson_key="A1_day1_ch1",
        pass_mark=60.0,
    )

    assert state["status_label"] == "In review"
    assert state["locked"] is True
    assert state["needs_resubmit"] is False
    assert state["from_scores"] is True
    assert state["clear_lock"] is False


def test_submit_status_completed(submit_status_helper, monkeypatch):
    helper, module = submit_status_helper
    monkeypatch.setattr(module, "fetch_latest_score", lambda *_: {"score": 85}, raising=False)

    state = helper(
        locked=True,
        needs_resubmit=True,
        latest_submission={"answer": "Hallo"},
        student_code="S1",
        lesson_key="A1_day1_ch1",
        pass_mark=60.0,
    )

    assert state["status_label"] == "Passed/Completed"
    assert state["needs_resubmit"] is False
    assert state["locked"] is True
    assert state["clear_lock"] is False


def test_submit_status_triggers_resubmit(submit_status_helper, monkeypatch):
    helper, module = submit_status_helper
    monkeypatch.setattr(module, "fetch_latest_score", lambda *_: {"score": 40}, raising=False)

    state = helper(
        locked=True,
        needs_resubmit=None,
        latest_submission={"answer": "Hallo"},
        student_code="S1",
        lesson_key="A1_day1_ch1",
        pass_mark=60.0,
    )

    assert state["status_label"] == "Resubmission needed"
    assert state["needs_resubmit"] is True
    assert state["locked"] is False
    assert state["clear_lock"] is True
