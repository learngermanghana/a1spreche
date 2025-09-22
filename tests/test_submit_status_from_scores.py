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


def test_assignment_score_fetch_and_status(submit_status_helper, monkeypatch):
    helper, module = submit_status_helper

    from src import firestore_helpers

    class FakeDoc:
        def __init__(self, data: Dict[str, Any]):
            self._data = data

        def to_dict(self) -> Dict[str, Any]:  # pragma: no cover - trivial proxy
            return dict(self._data)

    class FakeQuery:
        def __init__(self, docs: list[Dict[str, Any]]):
            self._docs = list(docs)

        def where(self, field: str, op: str, value: Any):
            assert op == "=="
            filtered = [doc for doc in self._docs if doc.get(field) == value]
            return FakeQuery(filtered)

        def stream(self):  # pragma: no cover - exercised in tests
            return [FakeDoc(doc) for doc in self._docs]

        def order_by(self, *_args, **_kwargs):  # pragma: no cover - compatibility
            return self

        def limit(self, *_args, **_kwargs):  # pragma: no cover - compatibility
            return self

    class FakeDB:
        def __init__(self, docs: list[Dict[str, Any]]):
            self._docs = list(docs)

        def collection(self, name: str):
            assert name == "scores"
            return FakeQuery(self._docs)

    docs = [
        {
            "student_code": "STU-1",
            "assignment": "A1 Assignment 4",
            "percentage": "70%",
            "updated_at": 150,
        },
        {
            "student_code": "STU-1",
            "assignment_name": "A1 Assignment 5",
            "percentage": "82%",
            "updated_at": 200,
            "status": "Completed",
        },
        {
            "student_code": "STU-2",
            "assignment_name": "A1 Assignment 5",
            "percentage": "90%",
            "updated_at": 250,
        },
    ]

    fake_db = FakeDB(docs)
    monkeypatch.setattr(firestore_helpers, "db", fake_db, raising=False)
    monkeypatch.setattr(firestore_helpers, "FieldFilter", None, raising=False)

    lesson_key = "A1_day5_chAssignment_5"

    score_doc = firestore_helpers.fetch_latest_score("STU-1", lesson_key, submission=None)

    assert score_doc is not None
    assert score_doc["numeric_score"] == pytest.approx(82.0)

    state = helper(
        locked=True,
        needs_resubmit=None,
        latest_submission={"answer": "Hallo"},
        student_code="STU-1",
        lesson_key=lesson_key,
        pass_mark=60.0,
        score_fetcher=firestore_helpers.fetch_latest_score,
    )

    assert state["status_label"] == "Passed/Completed"
    assert state["numeric_score"] == pytest.approx(82.0)
    assert state["needs_resubmit"] is False
