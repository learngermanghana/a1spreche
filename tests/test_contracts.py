import calendar
from datetime import datetime, UTC, timedelta

import pandas as pd


def parse_contract_end(date_str):
    if not date_str or str(date_str).strip().lower() in ("nan", "none", ""):
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def add_months(dt: datetime, n: int) -> datetime:
    """Add n calendar months to dt, clamping to month end if needed."""
    y = dt.year + (dt.month - 1 + n) // 12
    m = (dt.month - 1 + n) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    d = min(dt.day, last_day)
    return dt.replace(year=y, month=m, day=d)


def months_between(start_dt: datetime, end_dt: datetime) -> int:
    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    if end_dt.day < start_dt.day:
        months -= 1
    return months


def is_contract_expired(row):
    expiry_str = str(row.get("ContractEnd", "") or "").strip()
    if not expiry_str or expiry_str.lower() == "nan":
        return True
    expiry_date = None
    for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            expiry_date = datetime.strptime(expiry_str, fmt)
            break
        except ValueError:
            continue
    if expiry_date is None:
        parsed = pd.to_datetime(expiry_str, errors="coerce")
        if pd.isnull(parsed):
            return True
        expiry_date = parsed.to_pydatetime()
    return expiry_date.date() < datetime.now(UTC).date()


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
