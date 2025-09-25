from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.ui import auth


@dataclass
class DummyStreamlit:
    errors: list[str] = field(default_factory=list)
    session_state: dict[str, Any] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)

    def error(self, msg: str) -> None:
        self.errors.append(msg)


def test_login_refreshes_roster_on_initial_miss(monkeypatch):
    dummy_st = DummyStreamlit()
    monkeypatch.setattr(auth, "st", dummy_st)
    monkeypatch.setattr(auth, "renew_session_if_needed", lambda: None)
    monkeypatch.setattr(auth, "is_contract_expired", lambda row: False)

    captured_df: dict[str, Any] = {}

    def fake_contract_active(student_code: str, df: pd.DataFrame) -> bool:
        captured_df["df"] = df
        return False

    monkeypatch.setattr(auth, "contract_active", fake_contract_active)

    df_initial = pd.DataFrame(
        [
            {
                "StudentCode": "someoneelse",
                "Email": "other@example.com",
                "Name": "Other",
                "ContractEnd": "2024-01-01",
            }
        ]
    )
    df_refreshed = pd.DataFrame(
        [
            {
                "StudentCode": "matchcode",
                "Email": "target@example.com",
                "Name": "Target",
                "ContractEnd": "2025-01-01",
            }
        ]
    )

    calls: list[bool] = []

    def fake_loader(force_refresh: bool = False):
        calls.append(force_refresh)
        return df_refreshed.copy() if force_refresh else df_initial.copy()

    monkeypatch.setattr(auth, "load_student_data", fake_loader)

    ok = auth.render_login_form("target@example.com", "pw")

    assert ok is False
    assert calls == [False, True]
    assert dummy_st.errors[-1] == "Outstanding balance past due. Contact the office."
    assert "df" in captured_df
    assert captured_df["df"].iloc[0]["Email"] == "target@example.com"
