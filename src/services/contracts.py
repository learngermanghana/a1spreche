"""Contract-related helper functions."""

from datetime import UTC
from typing import Optional

import pandas as pd

from src.contracts import is_contract_expired


def contract_active(student_code: str, roster: Optional[pd.DataFrame]) -> bool:
    """Return True if the contract for ``student_code`` is still active.

    Parameters
    ----------
    student_code:
        Code identifying the student.
    roster:
        DataFrame containing at least ``StudentCode`` and contract fields.
    """
    if roster is None or "StudentCode" not in roster.columns:
        return True
    match = roster[roster["StudentCode"].str.lower() == student_code.lower()]
    if match.empty:
        return True
    row = match.iloc[0]
    if is_contract_expired(row):
        return False

    start_str = str(row.get("ContractStart", "") or "")
    start_date = pd.to_datetime(start_str, errors="coerce")
    if start_date is not pd.NaT:
        days_since_start = (pd.Timestamp.now(tz=UTC).date() - start_date.date()).days

        def _read_money(x: object) -> float:
            try:
                s = str(x).replace(",", "").replace(" ", "").strip()
                return float(s) if s not in ("", "nan", "None") else 0.0
            except Exception:
                return 0.0

        balance = _read_money(row.get("Balance", 0))
        if balance > 0 and days_since_start >= 30:
            return False

    return True

__all__ = ["contract_active"]
