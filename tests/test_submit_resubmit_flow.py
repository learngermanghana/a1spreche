import ast
import math
import re
import textwrap
import types
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple


def _load_resubmit_helpers():
    src_path = Path("a1sprechen.py")
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    class Finder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.positions: dict[str, tuple[int, int]] = {}

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pragma: no cover - AST traversal helper
            self.positions[node.name] = (node.lineno, node.end_lineno)
            self.generic_visit(node)

    finder = Finder()
    finder.visit(tree)

    start = finder.positions["_extract_assignment_numbers_for_resubmit"][0] - 1
    end = finder.positions["_should_abort_submission_for_existing_attempt"][1]
    snippet = textwrap.dedent("\n".join(source.splitlines()[start:end]))

    module = types.ModuleType("resubmit_helpers")
    module.re = re
    module.math = math
    module.Callable = Callable
    module.Any = Any
    module.Dict = Dict
    module.Iterable = Iterable
    module.List = List
    module.Optional = Optional
    module.Tuple = Tuple
    module.Set = Set
    module.MIN_RESUBMIT_WORD_COUNT = 20
    module._ASSIGNMENT_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")

    exec(snippet, module.__dict__)
    return module


def test_resubmit_unlocks_editor_when_summary_flags():
    helpers = _load_resubmit_helpers()
    unlock = helpers._compute_resubmit_unlock_state

    summary = {"failed_identifiers": [1.0]}
    lesson = {"assignment": True, "chapter": "1.0"}
    needs_resubmit, locked_after = unlock(
        True,
        summary=summary,
        lesson=lesson,
        answer_text="word " * 32,
        min_words=helpers.MIN_RESUBMIT_WORD_COUNT,
    )

    assert needs_resubmit is True
    assert locked_after is False


def test_resubmit_skip_already_submitted_warning():
    helpers = _load_resubmit_helpers()
    guard = helpers._should_abort_submission_for_existing_attempt

    abort, recovered = guard(
        needs_resubmit=True,
        got_lock=False,
        has_existing_submission_fn=lambda: True,
    )

    assert abort is False
    assert recovered is True

