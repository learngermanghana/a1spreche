import ast
import types
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def _load_score_helper_module():
    source = Path("a1sprechen.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    positions: Dict[str, tuple[int, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            positions[node.name] = (node.lineno, node.end_lineno)

    start, _ = positions["expected_assignment_name"]
    _, end = positions["get_score_for_assignment"]
    lines = source.splitlines()
    snippet = "\n".join(lines[start - 1 : end])

    module = types.ModuleType("score_helper_test")
    module.re = re
    module.Any = Any
    module.Dict = Dict
    module.List = List
    module.Optional = Optional
    module.Set = Set
    exec(snippet, module.__dict__)
    return module


class _StubDoc:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = dict(payload)

    def to_dict(self) -> Dict[str, Any]:  # pragma: no cover - trivial
        return dict(self._payload)


class _StubScoresCollection:
    def __init__(
        self,
        rows: List[Dict[str, Any]],
        recorded: List[str],
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._rows = list(rows)
        self._recorded = recorded
        self._filters = dict(filters or {})

    def where(self, *, filter):  # pragma: no cover - chaining helper
        field, _, value = filter
        new_filters = dict(self._filters)
        new_filters[field] = value
        return _StubScoresCollection(self._rows, self._recorded, new_filters)

    def limit(self, _):  # pragma: no cover - passthrough for chaining
        return self

    def stream(self):
        assignment_value = self._filters.get("assignment")
        if assignment_value is not None:
            self._recorded.append(assignment_value)

        results = []
        for row in self._rows:
            if all(row.get(field) == value for field, value in self._filters.items()):
                results.append(_StubDoc(row))
        return results


def test_get_score_for_assignment_matches_numeric_chapter():
    module = _load_score_helper_module()

    recorded: List[str] = []
    rows = [
        {
            "studentcode": "stu-001",
            "assignment": "1.5",
            "score": 88,
        }
    ]

    module.FieldFilter = lambda field, op, value: (field, op, value)
    module._scores_col = lambda: _StubScoresCollection(rows, recorded)

    lesson_info = {
        "chapter": "Kapitel 1.5",
        "lesen_hören": {"chapter": "1.5 Hörverständnis"},
        "schreiben_sprechen": {"chapter": "Schreiben 1.5"},
    }

    result = module.get_score_for_assignment(
        "stu-001",
        "B1",
        7,
        lesson_info=lesson_info,
    )

    assert result == rows[0]
    assert recorded == ["B1 Assignment 7", "7", "1.5"]
