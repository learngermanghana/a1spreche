import ast
import math
import re
import textwrap
import types
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


def _load_determine_needs_resubmit():
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    class Finder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.positions: Dict[str, tuple[int, int]] = {}

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pragma: no cover - ast traversal helper
            self.positions[node.name] = (node.lineno, node.end_lineno)
            self.generic_visit(node)

    finder = Finder()
    finder.visit(tree)

    start = finder.positions["_extract_assignment_numbers_for_resubmit"][0] - 1
    end = finder.positions["determine_needs_resubmit"][1]
    snippet = textwrap.dedent("\n".join(source.splitlines()[start:end]))

    mod = types.ModuleType("needs_resubmit_snippet")
    mod.re = re
    mod.math = math
    mod.Any = Any
    mod.Dict = Dict
    mod.Iterable = Iterable
    mod.List = List
    mod.Optional = Optional
    mod.Set = Set
    mod.MIN_RESUBMIT_WORD_COUNT = 20
    mod._ASSIGNMENT_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")

    exec(snippet, mod.__dict__)
    return mod.determine_needs_resubmit


def test_determine_needs_resubmit_flags_failed_identifier():
    determine = _load_determine_needs_resubmit()
    summary = {"failed_identifiers": [1.0]}
    lesson = {"assignment": True, "chapter": "1.0"}
    long_answer = "word " * 25

    assert determine(summary, lesson, answer_text=long_answer) is True


def test_determine_needs_resubmit_uses_word_count_fallback():
    determine = _load_determine_needs_resubmit()
    summary = {"failed_identifiers": []}
    lesson = {"assignment": True, "chapter": "5.0"}

    assert determine(summary, lesson, answer_text="too short", min_words=5) is True


def test_determine_needs_resubmit_detects_nested_assignment():
    determine = _load_determine_needs_resubmit()
    summary = {"failed_identifiers": [2.5]}
    lesson = {
        "assignment": False,
        "chapter": "2",
        "schreiben_sprechen": [
            {"assignment": True, "chapter": "2.5"},
        ],
    }
    long_answer = "word " * 25

    assert determine(summary, lesson, answer_text=long_answer) is True


def test_determine_needs_resubmit_skips_word_count_for_non_assignment():
    determine = _load_determine_needs_resubmit()
    summary = {"failed_identifiers": []}
    lesson = {"assignment": False, "chapter": "intro"}

    assert determine(summary, lesson, answer_text="", min_words=5) is False
