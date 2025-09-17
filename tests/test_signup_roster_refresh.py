from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.ui import auth


@dataclass
class DummyDocRef:
    code: str | None = None
    data: dict[str, Any] | None = None

    class _NotExists:
        exists = False

    def get(self) -> DummyDocRef._NotExists:  # type: ignore[name-defined]
        return self._NotExists()

    def set(self, data: dict[str, Any]) -> None:
        self.data = data


@dataclass
class DummyDB:
    doc: DummyDocRef = field(default_factory=DummyDocRef)

    def collection(self, name: str) -> DummyDB:  # type: ignore[override]
        assert name == "students"
        return self

    def document(self, code: str) -> DummyDocRef:
        self.doc.code = code
        return self.doc


@dataclass
class DummyFormContext:
    def __enter__(self) -> DummyFormContext:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401 - signature enforced by context manager protocol
        return None


@dataclass
class DummyStreamlit:
    inputs: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    successes: list[str] = field(default_factory=list)
    session_state: dict[str, Any] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)

    def form(self, *args, **kwargs) -> DummyFormContext:
        return DummyFormContext()

    def text_input(self, label: str, *, key: str | None = None, **kwargs) -> str:
        if key and key in self.inputs:
            return self.inputs[key]
        return self.inputs.get(label, "")

    def form_submit_button(self, label: str) -> bool:
        return bool(self.inputs.get("submit", False))

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def success(self, msg: str) -> None:
        self.successes.append(msg)


def test_signup_refreshes_roster_on_initial_miss(monkeypatch):
    dummy_db = DummyDB()
    inputs = {
        "ca_name": "Target Person",
        "ca_email": "Target@Example.com ",
        "ca_code": "MatchCode ",
        "ca_pass": "strongpass",
        "submit": True,
    }
    dummy_st = DummyStreamlit(inputs=inputs)
    dummy_st.session_state["db"] = dummy_db

    monkeypatch.setattr(auth, "st", dummy_st)
    monkeypatch.setattr(auth, "renew_session_if_needed", lambda: None)

    df_initial = pd.DataFrame(
        [
            {
                "StudentCode": "someoneelse",
                "Email": "other@example.com",
                "Name": "Other",
            }
        ]
    )
    df_refreshed = pd.DataFrame(
        [
            {
                "StudentCode": "matchcode",
                "Email": "target@example.com",
                "Name": "Target Person",
            }
        ]
    )

    calls: list[bool] = []

    def fake_loader(force_refresh: bool = False):
        calls.append(force_refresh)
        return df_refreshed.copy() if force_refresh else df_initial.copy()

    monkeypatch.setattr(auth, "load_student_data", fake_loader)

    auth.render_signup_form()

    assert calls == [False, True]
    assert dummy_st.errors == []
    assert dummy_st.successes == ["Account created! Please log in on the Returning tab."]
    assert dummy_db.doc.code == "matchcode"
    assert dummy_db.doc.data is not None
    assert dummy_db.doc.data["email"] == "target@example.com"
