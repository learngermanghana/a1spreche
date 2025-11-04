"""Utilities for handling contract dates and status."""

import calendar
from datetime import datetime, UTC
import pandas as pd


def parse_contract_end(date_str):
    """Parse a contract end date in multiple common formats."""
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
    """Return True if the row's ContractEnd date is in the past or invalid."""
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
