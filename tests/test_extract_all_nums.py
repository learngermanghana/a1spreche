import types

import pytest

from src import assignment_ui
from src.assignment_ui import get_assignment_summary


def _get_extract_all_nums():
    code_obj = next(
        const
        for const in get_assignment_summary.__code__.co_consts
        if isinstance(const, types.CodeType) and const.co_name == "_extract_all_nums"
    )
    return types.FunctionType(code_obj, assignment_ui.__dict__)


@pytest.mark.parametrize(
    "chapter_str, expected",
    [
        ("0.2 and 1.1", [0.2, 1.1]),
        ("12.1,2,3", [12.1, 12.2, 12.3]),
    ],
)
def test_extract_all_nums(chapter_str: str, expected: list[float]) -> None:
    extract = _get_extract_all_nums()
    assert extract(chapter_str) == expected

