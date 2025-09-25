import ast
import math
import sys
from pathlib import Path
from datetime import date, datetime, UTC, timedelta
from typing import Any

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.contracts import parse_contract_end, add_months, months_between, is_contract_expired


def _load_contract_date_helpers():
    src_path = Path(__file__).resolve().parents[1] / "a1sprechen.py"
    source = src_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename="a1sprechen.py")

    wanted = {
        "CONTRACT_DATE_FORMATS",
        "_parse_contract_date_value",
        "parse_contract_start",
        "_compute_finish_date_estimates",
    }
    nodes: list[Any] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "CONTRACT_DATE_FORMATS" for t in node.targets):
                nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name in wanted:
            nodes.append(node)

    module = ast.Module(body=nodes, type_ignores=[])
    glb = {
        "Any": Any,
        "datetime": datetime,
        "UTC": UTC,
        "timedelta": timedelta,
        "date": date,
    }
    exec(compile(module, "a1sprechen.py", "exec"), glb)
    return glb["parse_contract_start"], glb["_compute_finish_date_estimates"]


def test_parse_contract_end_formats():
    expected = datetime(2023, 5, 1)
    assert parse_contract_end("2023-05-01") == expected
    assert parse_contract_end("05/01/2023") == expected
    assert parse_contract_end("01.05.23") == expected
    assert parse_contract_end("01-05-2023") == expected
    # day/month/year format where month > 12 to ensure correct parsing
    assert parse_contract_end("31/05/2023") == datetime(2023, 5, 31)
    assert parse_contract_end("invalid") is None
    assert parse_contract_end("") is None


def test_parse_contract_start_handles_extended_formats():
    parse_contract_start, _ = _load_contract_date_helpers()
    expected = datetime(2023, 5, 1)
    assert parse_contract_start("01.05.2023") == expected
    assert parse_contract_start("01.05.2023 00:00:00") == expected
    assert parse_contract_start("2023-05-01 07:30:00") == datetime(2023, 5, 1, 7, 30)
    assert parse_contract_start("2023-05-01T07:30:00") == datetime(2023, 5, 1, 7, 30)
    assert parse_contract_start("2023-05-01T07:30:00Z") == datetime(2023, 5, 1, 7, 30)


def test_course_overview_estimates_available_for_new_start_formats():
    parse_contract_start, compute_finish = _load_contract_date_helpers()
    total_lessons = 6
    start = datetime(2023, 5, 1).date()

    iso_estimates = compute_finish("2023-05-01T00:00:00", total_lessons, parse_contract_start)
    dot_estimates = compute_finish("01.05.2023", total_lessons, parse_contract_start)
    iso_z_estimates = compute_finish("2023-05-01T00:00:00Z", total_lessons, parse_contract_start)

    assert iso_estimates is not None
    assert dot_estimates == iso_estimates
    assert iso_z_estimates == iso_estimates
    assert iso_estimates[3] == start + timedelta(weeks=(total_lessons + 2) // 3)
    assert iso_estimates[2] == start + timedelta(weeks=(total_lessons + 1) // 2)
    assert iso_estimates[1] == start + timedelta(weeks=total_lessons)


def test_finish_estimates_use_personalised_pace_and_anchor():
    parse_contract_start, compute_finish = _load_contract_date_helpers()
    total_lessons = 20
    anchor = datetime(2024, 3, 1).date()

    estimates = compute_finish(
        "2024-01-01",
        total_lessons,
        parse_contract_start,
        pace_sessions_per_week=2.5,
        completed_lessons=5,
        anchor_date=anchor,
    )

    assert estimates is not None
    remaining = total_lessons - 5
    expected_current = anchor + timedelta(weeks=math.ceil(remaining / 2.5))
    expected_plus_one = anchor + timedelta(weeks=math.ceil(remaining / 3.5))
    expected_double = anchor + timedelta(weeks=math.ceil(remaining / 5.0))

    assert estimates["current"] == expected_current
    assert estimates["plus_one"] == expected_plus_one
    assert estimates["double"] == expected_double


def test_add_months_and_months_between():
    assert add_months(datetime(2023, 1, 31), 1) == datetime(2023, 2, 28)
    assert add_months(datetime(2024, 1, 31), 1) == datetime(2024, 2, 29)
    start = datetime(2024, 1, 15)
    end_early = datetime(2024, 3, 14)
    end_exact = datetime(2024, 3, 15)
    assert months_between(start, end_early) == 1
    assert months_between(start, end_exact) == 2


def test_is_contract_expired():
    past = {"ContractEnd": "01/01/2000"}
    future_date = (datetime.now(UTC) + timedelta(days=30)).strftime("%Y-%m-%d")
    future = {"ContractEnd": future_date}
    assert is_contract_expired(past) is True
    assert is_contract_expired(future) is False
