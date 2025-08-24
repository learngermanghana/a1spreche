import sys
from pathlib import Path
from datetime import datetime, UTC, timedelta

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.contracts import parse_contract_end, add_months, months_between, is_contract_expired

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
